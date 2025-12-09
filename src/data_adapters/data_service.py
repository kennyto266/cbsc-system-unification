"""
數據服務管理器 - 統一管理多個真實數據源

支持Yahoo Finance、Alpha Vantage、CCXT等多個數據源
"""

import asyncio
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import json

from .base_adapter import (
BaseDataAdapter, 
DataAdapterConfig, 
RealMarketData, 
DataValidationResult,
DataSourceType
)
from .yahoo_finance_adapter import YahooFinanceAdapter
from .alpha_vantage_adapter import AlphaVantageAdapter
from .ccxt_crypto_adapter import CCXTCryptoAdapter
from .raw_data_adapter import RawDataAdapter
from .http_api_adapter import HttpApiDataAdapter

class DataService:
"""數據服務管理器"""

def __init__self, config_path: str = "config/data_adapters.json":    self.config_path = config_path
self.logger = logging.getLogger"hk_quant_system.data_service"
self.adapters: Dict[str, BaseDataAdapter] = {}
self.adapter_configs: Dict[str, Dict] = {}
self._initialized = False

async def initializeself -> bool:
"""初始化數據服務"""
try:
self.logger.info"Initializing data service..."

await self._load_config()

await self._initialize_adapters()

self._initialized = True
self.logger.info"Data service initialized successfully"
return True

except Exception as e:
self.logger.exceptionf"Failed to initialize data service: {e}"
return False

async def _load_configself -> None:
"""加載配置"""
try:    config_file = Path(self.config_path)
if not config_file.exists():
self.logger.warningf"Config file not found: {self.config_path}"
await self._create_default_config()
return

with openconfig_file, 'r', encoding='utf-8' as f:    config_data = json.load(f)

self.adapter_configs = {}
for adapter_config in config_data.get'adapters', []:    name = adapter_config['name']
if adapter_config.get'enabled', True:    self.adapter_configs[name] = adapter_config
self.logger.infof"Loaded adapter config: {name}"
else:
self.logger.infof"Skipping disabled adapter: {name}"

except Exception as e:
self.logger.errorf"Error loading config: {e}"
await self._create_default_config()

async def _create_default_configself -> None:
"""創建默認配置"""
try:    config_dir = Path(self.config_path).parent
config_dir.mkdirparents=True, exist_ok=True

default_config = {
"adapters": [
{
"name": "yahoo_finance",
"enabled": True,
"priority": 1,
"config": {
"source_type": "yahoo_finance",
"source_path": "https://finance.yahoo.com",
"update_frequency": 60,
"max_retries": 3,
"timeout": 30,
"cache_enabled": True,
"cache_ttl": 300,
"quality_threshold": 0.8
}
},
{
"name": "alpha_vantage",
"enabled": False, # 需要API密鑰
"priority": 2,
"config": {
"source_type": "alpha_vantage",
"source_path": "https://www.alphavantage.co",
"api_key": "YOUR_API_KEY_HERE",
"update_frequency": 60,
"max_retries": 3,
"timeout": 30,
"cache_enabled": True,
"cache_ttl": 300,
"quality_threshold": 0.8
}
},
{
"name": "binance_crypto",
"enabled": True,
"priority": 3,
"config": {
"source_type": "custom",
"source_path": "https://api.binance.com",
"exchange": "binance",
"sandbox": True,
"api_key": None,
"secret": None,
"update_frequency": 30,
"max_retries": 3,
"timeout": 30,
"cache_enabled": True,
"cache_ttl": 60,
"quality_threshold": 0.8
}
}
]
}

with openself.config_path, 'w', encoding='utf-8' as f:    json.dump(default_config, f, indent=2, ensure_ascii=False)

self.logger.infof"Created default config: {self.config_path}"

except Exception as e:
self.logger.errorf"Error creating default config: {e}"

async def _initialize_adaptersself -> None:
"""初始化適配器"""
try:
for name, config in self.adapter_configs.items():
try:    adapter = await self._create_adapter(name, config)
if adapter:    self.adapters[name] = adapter
self.logger.infof"Initialized adapter: {name}"
else:
self.logger.warningf"Failed to initialize adapter: {name}"

except Exception as e:
self.logger.errorf"Error initializing adapter {name}: {e}"

except Exception as e:
self.logger.errorf"Error initializing adapters: {e}"

async def _create_adapterself, name: str, config: Dict -> Optional[BaseDataAdapter]:
"""創建適配器實例"""
try:    adapter_config = DataAdapterConfig(**config['config'])

# 根據數據源類型創建相應的適配器
if adapter_config.source_type == DataSourceType.YAHOO_FINANCE:
return YahooFinanceAdapteradapter_config
elif adapter_config.source_type == DataSourceType.ALPHA_VANTAGE:
return AlphaVantageAdapteradapter_config
elif adapter_config.source_type == DataSourceType.RAW_DATA:
return RawDataAdapteradapter_config
elif adapter_config.source_type == DataSourceType.HTTP_API:
return HttpApiDataAdapteradapter_config
elif adapter_config.source_type == DataSourceType.CUSTOM:
# 檢查是否為加密貨幣適配器
if config['config'].get'exchange':
return CCXTCryptoAdapteradapter_config
else:
self.logger.warningf"Unknown custom adapter type: {name}"
return None
else:
self.logger.warningf"Unknown adapter type: {adapter_config.source_type}"
return None

except Exception as e:
self.logger.errorf"Error creating adapter {name}: {e}"
return None

async def get_market_data(
self, 
symbol: str, 
start_date: Optional[date] = None,
end_date: Optional[date] = None,
preferred_adapter: Optional[str] = None
) -> List[RealMarketData]:
"""獲取市場數據"""
if not self._initialized:
self.logger.error"Data service not initialized"
return []

try:
# 如果指定了優先適配器，先嘗試該適配器
if preferred_adapter and preferred_adapter in self.adapters:    adapter = self.adapters[preferred_adapter]
if await adapter.connect():    data = await adapter.get_market_data(symbol, start_date, end_date)
if data:
self.logger.infof"Got data from preferred adapter: {preferred_adapter}"
return data

# 按優先級嘗試所有適配器
sorted_adapters = sorted(
self.adapters.items(),
key=lambda x: self.adapter_configs[x[0]].get'priority', 999
)

for adapter_name, adapter in sorted_adapters:
try:
if await adapter.connect():    data = await adapter.get_market_data(symbol, start_date, end_date)
if data:
self.logger.infof"Got data from adapter: {adapter_name}"
return data
else:
self.logger.debugf"No data from adapter: {adapter_name}"
else:
self.logger.warningf"Failed to connect to adapter: {adapter_name}"

except Exception as e:
self.logger.errorf"Error with adapter {adapter_name}: {e}"
continue

self.logger.warningf"No data found for symbol: {symbol}"
return []

except Exception as e:
self.logger.errorf"Error getting market data: {e}"
return []

async def get_real_time_data(
self, 
symbol: str, 
preferred_adapter: Optional[str] = None
) -> Optional[RealMarketData]:
"""獲取實時數據"""
if not self._initialized:
self.logger.error"Data service not initialized"
return None

try:
# 如果指定了優先適配器，先嘗試該適配器
if preferred_adapter and preferred_adapter in self.adapters:    adapter = self.adapters[preferred_adapter]
if await adapter.connect():    data = await adapter.get_real_time_data(symbol)
if data:
return data

# 按優先級嘗試所有適配器
sorted_adapters = sorted(
self.adapters.items(),
key=lambda x: self.adapter_configs[x[0]].get'priority', 999
)

for adapter_name, adapter in sorted_adapters:
try:
if await adapter.connect():    data = await adapter.get_real_time_data(symbol)
if data:
return data

except Exception as e:
self.logger.errorf"Error with adapter {adapter_name}: {e}"
continue

return None

except Exception as e:
self.logger.errorf"Error getting real-time data: {e}"
return None

async def get_multiple_symbols_data(
self, 
symbols: List[str], 
start_date: Optional[date] = None,
end_date: Optional[date] = None,
preferred_adapter: Optional[str] = None
) -> Dict[str, List[RealMarketData]]:
"""批量獲取多個標的數據"""
try:

tasks = [
self.get_market_datasymbol, start_date, end_date, preferred_adapter
for symbol in symbols
]

results = await asyncio.gather*tasks, return_exceptions=True

symbol_data = {}
for symbol, result in zipsymbols, results:
if isinstanceresult, Exception:
self.logger.errorf"Error fetching data for {symbol}: {result}"
symbol_data[symbol] = []
else:    symbol_data[symbol] = result

successful_symbols = len([s for s, data in symbol_data.items() if data])
self.logger.info(f"Successfully fetched data for {successful_symbols}/{lensymbols} symbols")

return symbol_data

except Exception as e:
self.logger.errorf"Error fetching multiple symbols data: {e}"
return {}

async def search_symbolsself, query: str -> List[Dict[str, Any]]:
"""搜索標的符號"""
try:    all_results = []

# 從所有適配器搜索
for adapter_name, adapter in self.adapters.items():
try:
if await adapter.connect():    results = await adapter.search_symbols(query)
for result in results:    result['adapter'] = adapter_name
all_results.extendresults

except Exception as e:
self.logger.errorf"Error searching with adapter {adapter_name}: {e}"
continue

unique_results = []
seen_symbols = set()

for result in all_results:    symbol = result.get('symbol', '')
if symbol not in seen_symbols:
seen_symbols.addsymbol
unique_results.appendresult

return unique_results[:50] # 限制結果數量

except Exception as e:
self.logger.errorf"Error searching symbols: {e}"
return []

async def get_adapter_statusself -> Dict[str, Any]:
"""獲取所有適配器狀態"""
try:    status = {}

for adapter_name, adapter in self.adapters.items():
try:    health_info = await adapter.health_check()
status[adapter_name] = {
"status": health_info.get"status", "unknown",
"source_type": health_info.get"source_type", "unknown",
"last_update": health_info.get"last_update",
"cache_size": health_info.get"cache_size", 0,
"config": health_info.get"config", {}
}
except Exception as e:    status[adapter_name] = {
"status": "error",
"error": stre
}

return status

except Exception as e:
self.logger.errorf"Error getting adapter status: {e}"
return {}

async def validate_data_quality(
self, 
symbol: str, 
start_date: Optional[date] = None,
end_date: Optional[date] = None
) -> Dict[str, DataValidationResult]:
"""驗證所有適配器的數據質量"""
try:    validation_results = {}

for adapter_name, adapter in self.adapters.items():
try:
if await adapter.connect():    data = await adapter.get_market_data(symbol, start_date, end_date)
if data:    validation_result = await adapter.validate_data(data)
validation_results[adapter_name] = validation_result
else:    validation_results[adapter_name] = DataValidationResult(
is_valid=False,
quality_score=0.0,
quality_level="unknown",
errors=["No data available"],
warnings=[]
)

except Exception as e:    validation_results[adapter_name] = DataValidationResult(
is_valid=False,
quality_score=0.0,
quality_level="unknown",
errors=[f"Adapter error: {stre}"],
warnings=[]
)

return validation_results

except Exception as e:
self.logger.errorf"Error validating data quality: {e}"
return {}

async def cleanupself -> None:
"""清理資源"""
try:
for adapter_name, adapter in self.adapters.items():
try:
await adapter.disconnect()
self.logger.infof"Disconnected adapter: {adapter_name}"
except Exception as e:
self.logger.errorf"Error disconnecting adapter {adapter_name}: {e}"

self.adapters.clear()
self.adapter_configs.clear()
self._initialized = False

self.logger.info"Data service cleanup completed"

except Exception as e:
self.logger.errorf"Error during cleanup: {e}"

def get_available_adaptersself -> List[str]:
"""獲取可用的適配器列表"""
return list(self.adapters.keys())

def get_adapter_infoself, adapter_name: str -> Optional[Dict]:
"""獲取適配器信息"""
if adapter_name in self.adapter_configs:
return self.adapter_configs[adapter_name]
return None
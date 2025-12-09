#!/usr/bin/env python3
"""
香港市場專用數據管理器 - Hong Kong Exclusive Market Data Manager
專注於香港股票市場的數據提取、處理和緩存
Hong Kong Exclusive Market Data Manager - Focused on Hong Kong Stock Market Data Extraction, Processing and Caching
"""

import asyncio
import aiohttp
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import numpy as np
from pathlib import Path
import pickle
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

# Setup logging
logger = logging.getLogger(__name__)

class HKDataSourceStatus(Enum):
    """香港數據源狀態枚舉"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DISABLED = "disabled"

class HKDataSourcePriority(Enum):
    """香港數據源優先級枚舉"""
    PRIMARY = 1      # 香港交易所官方數據
    SECONDARY = 2    # 金管局API
    TERTIARY = 3     # Yahoo Finance香港
    FALLBACK = 4     # Alpha Vantage

@dataclass
class HKDataSourceConfig:
    """香港數據源配置"""
    name: str
    source_type: str  # 'stock', 'economic', 'hibor', 'monetary'
    url: str
    priority: HKDataSourcePriority
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    enabled: bool = True
    api_key: Optional[str] = None
    rate_limit: int = 100  # requests per minute

@dataclass
class HKMarketData:
    """香港市場數據模型"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    market_cap: Optional[float] = None
    currency: str = "HKD"
    asset_class: str = "equity"

class HKMarketDataManager:
    """香港市場專用數據管理器"""

    def __init__(self, config_path: Optional[str] = None):
        self.data_sources: Dict[str, HKDataSourceConfig] = {}
        self.cache = {}
        self.cache_ttl = 300  # 5分鐘緩存
        self.session = None
        self.last_request_time = {}
        self.rate_limit_window = 60  # 1分鐘窗口

        # 初始化香港專用數據源
        self._initialize_hk_data_sources()

        if config_path:
            self._load_config(config_path)

    def _initialize_hk_data_sources(self):
        """初始化香港專用數據源"""

        # 香港金管局API數據源
        self.data_sources["hkma_hibor"] = HKDataSourceConfig(
            name="香港金管局HIBOR",
            source_type="economic",
            url="https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily",
            priority=HKDataSourcePriority.SECONDARY,
            timeout=30,
            rate_limit=60
        )

        self.data_sources["hkma_monetary"] = HKDataSourceConfig(
            name="香港金管局貨幣基礎",
            source_type="economic",
            url="https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base",
            priority=HKDataSourcePriority.SECONDARY,
            timeout=30,
            rate_limit=60
        )

        self.data_sources["hkma_exchange"] = HKDataSourceConfig(
            name="香港金管局匯率",
            source_type="economic",
            url="https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/er-eeri-daily",
            priority=HKDataSourcePriority.SECONDARY,
            timeout=30,
            rate_limit=60
        )

        # Yahoo Finance香港（用於股票數據）
        self.data_sources["yahoo_hk"] = HKDataSourceConfig(
            name="Yahoo Finance香港",
            source_type="stock",
            url="https://query1.finance.yahoo.com/v8/finance/chart/",
            priority=HKDataSourcePriority.TERTIARY,
            timeout=15,
            rate_limit=100
        )

        # Alpha Vantage（備用股票數據）
        self.data_sources["alpha_vantage"] = HKDataSourceConfig(
            name="Alpha Vantage",
            source_type="stock",
            url="https://www.alphavantage.co/query",
            priority=HKDataSourcePriority.FALLBACK,
            timeout=30,
            rate_limit=5  # 免費版限制
        )

    async def _check_rate_limit(self, source_id: str):
        """檢查速率限制"""
        current_time = time.time()
        last_time = self.last_request_time.get(source_id, 0)

        # 如果距離上次請求時間小於窗口期，等待
        if current_time - last_time < self.rate_limit_window / len(self.data_sources):
            wait_time = self.rate_limit_window / len(self.data_sources) - (current_time - last_time)
            await asyncio.sleep(wait_time)

        self.last_request_time[source_id] = time.time()

    async def _fetch_from_source(self, source_config: HKDataSourceConfig, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """從指定數據源獲取數據"""
        await self._check_rate_limit(source_config.name)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        if source_config.api_key:
            headers['Authorization'] = f'Bearer {source_config.api_key}'

        try:
            if self.session is None:
                self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=source_config.timeout))

            async with self.session.get(source_config.url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"HTTP {response.status} from {source_config.name}")
                    return {}

        except Exception as e:
            logger.error(f"Error fetching from {source_config.name}: {e}")
            return {}

    async def get_hk_stock_data(self, symbols: List[str]) -> Dict[str, HKMarketData]:
        """獲取香港股票數據"""
        results = {}

        # 創建任務列表
        tasks = []
        for symbol in symbols:
            if not symbol.endswith('.HK'):
                symbol = f"{symbol}.HK"
            tasks.append(self._get_stock_data(symbol))

        # 並發執行
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(completed_tasks):
            symbol = symbols[i]
            if not symbol.endswith('.HK'):
                symbol = f"{symbol}.HK"

            if isinstance(result, HKMarketData):
                results[symbol] = result
            else:
                logger.error(f"Failed to get data for {symbol}: {result}")

        return results

    async def _get_stock_data(self, symbol: str) -> HKMarketData:
        """獲取單個股票數據"""
        cache_key = f"stock_{symbol}"

        # 檢查緩存
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return cached_data

        # 按優先級嘗試數據源
        for source_config in sorted(self.data_sources.values(), key=lambda x: x.priority.value):
            if source_config.source_type != "stock" or not source_config.enabled:
                continue

            try:
                if source_config.name == "Yahoo Finance香港":
                    data = await self._fetch_yahoo_stock_data(symbol, source_config)
                elif source_config.name == "Alpha Vantage":
                    data = await self._fetch_alpha_vantage_data(symbol, source_config)
                else:
                    continue

                if data:
                    market_data = self._parse_stock_data(symbol, data)
                    self.cache[cache_key] = (market_data, datetime.now())
                    return market_data

            except Exception as e:
                logger.warning(f"Failed to fetch {symbol} from {source_config.name}: {e}")
                continue

        raise ValueError(f"No data available for {symbol}")

    async def _fetch_yahoo_stock_data(self, symbol: str, config: HKDataSourceConfig) -> Dict[str, Any]:
        """從Yahoo Finance獲取股票數據"""
        params = {
            'symbol': symbol.replace('.HK', '') + '.HK',
            'interval': '1d',
            'range': '5d'  # 獲取最近5天數據
        }

        data = await self._fetch_from_source(config, params)

        if data and 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
            return data['chart']['result'][0]

        return {}

    async def _fetch_alpha_vantage_data(self, symbol: str, config: HKDataSourceConfig) -> Dict[str, Any]:
        """從Alpha Vantage獲取股票數據"""
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol.replace('.HK', '.HKG'),  # Alpha Vantage使用.HKG
            'apikey': config.api_key or 'demo'  # 使用demo key作為備用
        }

        data = await self._fetch_from_source(config, params)

        if data and 'Time Series (Daily)' in data:
            return data['Time Series (Daily)']

        return {}

    def _parse_stock_data(self, symbol: str, raw_data: Dict[str, Any]) -> HKMarketData:
        """解析股票數據"""
        try:
            if 'timestamp' in raw_data and 'indicators' in raw_data:
                # Yahoo Finance格式
                timestamps = raw_data['timestamp']
                quote_data = raw_data['indicators']['quote'][0]

                # 獲取最新數據
                if timestamps and quote_data['close']:
                    latest_index = len(timestamps) - 1
                    latest_timestamp = datetime.fromtimestamp(timestamps[latest_index])

                    return HKMarketData(
                        symbol=symbol,
                        timestamp=latest_timestamp,
                        open=quote_data['open'][latest_index] or 0,
                        high=quote_data['high'][latest_index] or 0,
                        low=quote_data['low'][latest_index] or 0,
                        close=quote_data['close'][latest_index] or 0,
                        volume=quote_data['volume'][latest_index] or 0,
                        currency="HKD",
                        asset_class="equity"
                    )

            elif isinstance(raw_data, dict) and list(raw_data.values())[0]:
                # Alpha Vantage格式
                latest_date = list(raw_data.keys())[0]
                latest_data = list(raw_data.values())[0]

                return HKMarketData(
                    symbol=symbol,
                    timestamp=datetime.strptime(latest_date, '%Y-%m-%d'),
                    open=float(latest_data['1. open']),
                    high=float(latest_data['2. high']),
                    low=float(latest_data['3. low']),
                    close=float(latest_data['4. close']),
                    volume=int(latest_data['5. volume']),
                    currency="HKD",
                    asset_class="equity"
                )

        except Exception as e:
            logger.error(f"Error parsing stock data for {symbol}: {e}")

        raise ValueError(f"Could not parse stock data for {symbol}")

    async def get_hkma_economic_data(self, data_type: str = "hibor") -> Dict[str, Any]:
        """獲取香港金管局經濟數據"""
        source_mapping = {
            "hibor": "hkma_hibor",
            "monetary": "hkma_monetary",
            "exchange": "hkma_exchange"
        }

        source_id = source_mapping.get(data_type)
        if not source_id or source_id not in self.data_sources:
            raise ValueError(f"Unknown HKMA data type: {data_type}")

        source_config = self.data_sources[source_id]
        data = await self._fetch_from_source(source_config)

        return self._parse_hkma_data(data, data_type)

    def _parse_hkma_data(self, raw_data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """解析香港金管局數據"""
        try:
            if 'result' in raw_data and 'records' in raw_data['result']:
                records = raw_data['result']['records']

                if records:
                    # 返回最新記錄
                    latest_record = records[0] if isinstance(records, list) else records
                    return {
                        'data_type': data_type,
                        'timestamp': latest_record.get('end_of_day', datetime.now().isoformat()),
                        'value': latest_record.get('value'),
                        'source': 'HKMA',
                        'metadata': latest_record
                    }

            return {'data_type': data_type, 'error': 'No valid data found'}

        except Exception as e:
            logger.error(f"Error parsing HKMA data ({data_type}): {e}")
            return {'data_type': data_type, 'error': str(e)}

    async def get_hsi_constituents_data(self) -> List[str]:
        """獲取恆生指數成分股列表"""
        cache_key = "hsi_constituents"

        # 檢查緩存
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(hours=24):  # HSI成分股24小時緩存
                return cached_data

        # 從本地文件讀取
        try:
            hsi_file = Path(__file__).parent.parent.parent.parent / "data" / "cache" / "hsi_constituents.json"
            if hsi_file.exists():
                with open(hsi_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    symbols = data.get('symbols', [])

                    # 緩存結果
                    self.cache[cache_key] = (symbols, datetime.now())
                    return symbols
            else:
                logger.warning("HSI constituents file not found, using default symbols")
                default_symbols = ["0700.HK", "0941.HK", "1299.HK", "2318.HK", "0388.HK"]
                self.cache[cache_key] = (default_symbols, datetime.now())
                return default_symbols

        except Exception as e:
            logger.error(f"Error loading HSI constituents: {e}")
            return ["0700.HK", "0941.HK", "1299.HK", "2318.HK", "0388.HK"]

    async def get_all_hk_market_data(self) -> Dict[str, Any]:
        """獲取所有香港市場數據"""
        # 獲取HSI成分股
        hsi_symbols = await self.get_hsi_constituents_data()

        # 獲取股票數據
        stock_data = await self.get_hk_stock_data(hsi_symbols[:10])  # 限制前10個以避免超時

        # 獲取經濟數據
        hibor_data = await self.get_hkma_economic_data("hibor")
        monetary_data = await self.get_hkma_economic_data("monetary")
        exchange_data = await self.get_hkma_economic_data("exchange")

        return {
            'timestamp': datetime.now().isoformat(),
            'stock_data': {symbol: asdict(data) for symbol, data in stock_data.items()},
            'economic_data': {
                'hibor': hibor_data,
                'monetary': monetary_data,
                'exchange': exchange_data
            },
            'sources_used': len([s for s in self.data_sources.values() if s.enabled]),
            'hsi_constituents_count': len(hsi_symbols)
        }

    def clear_cache(self):
        """清除緩存"""
        self.cache.clear()
        logger.info("HK market data cache cleared")

    def get_source_status(self) -> Dict[str, Dict[str, Any]]:
        """獲取數據源狀態"""
        status = {}

        for source_id, config in self.data_sources.items():
            status[source_id] = {
                'name': config.name,
                'type': config.source_type,
                'priority': config.priority.name,
                'enabled': config.enabled,
                'rate_limit': config.rate_limit,
                'last_request': self.last_request_time.get(source_id, 0)
            }

        return status

    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'healthy_sources': 0,
            'total_sources': len([s for s in self.data_sources.values() if s.enabled]),
            'details': {}
        }

        # 檢查每個數據源
        for source_id, config in self.data_sources.items():
            if not config.enabled:
                continue

            try:
                start_time = time.time()
                data = await self._fetch_from_source(config)
                response_time = time.time() - start_time

                if data:
                    results['details'][source_id] = {
                        'status': 'healthy',
                        'response_time': response_time,
                        'last_check': datetime.now().isoformat()
                    }
                    results['healthy_sources'] += 1
                else:
                    results['details'][source_id] = {
                        'status': 'unhealthy',
                        'response_time': response_time,
                        'last_check': datetime.now().isoformat(),
                        'error': 'No data returned'
                    }

            except Exception as e:
                results['details'][source_id] = {
                    'status': 'unhealthy',
                    'last_check': datetime.now().isoformat(),
                    'error': str(e)
                }

        results['overall_health'] = results['healthy_sources'] / results['total_sources'] if results['total_sources'] > 0 else 0

        return results

    async def close(self):
        """關閉連接"""
        if self.session:
            await self.session.close()
            self.session = None

# 全局實例
_hk_data_manager = None

def get_hk_market_data_manager() -> HKMarketDataManager:
    """獲取香港市場數據管理器單例"""
    global _hk_data_manager
    if _hk_data_manager is None:
        _hk_data_manager = HKMarketDataManager()
    return _hk_data_manager

# 使用示例
async def example_usage():
    """使用示例"""
    manager = get_hk_market_data_manager()

    try:
        # 獲取特定股票數據
        stock_data = await manager.get_hk_stock_data(['0700', '0941', '1299'])
        print(f"Stock data: {stock_data}")

        # 獲取HIBOR數據
        hibor_data = await manager.get_hkma_economic_data("hibor")
        print(f"HIBOR data: {hibor_data}")

        # 健康檢查
        health = await manager.health_check()
        print(f"Health check: {health}")

        # 獲取所有香港市場數據
        all_data = await manager.get_all_hk_market_data()
        print(f"All HK market data keys: {all_data.keys()}")

    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(example_usage())
#!/usr/bin/env python3
"""
多资产数据适配器 - Multi-Asset Data Adapter
统一外汇、商品、加密货币数据获取接口
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
import requests
from pathlib import Path
import pickle
import hashlib

from .asset_models import (
    AssetClass, MarketRegion, Timeframe, Exchange,
    MarketData, TickerInfo, parse_symbol, get_trading_hours
)

# Setup logging
logger = logging.getLogger(__name__)

class DataSourceStatus(Enum):
    """数据源状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"

@dataclass
class DataSourceConfig:
    """数据源配置"""
    name: str
    url: str
    api_key: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit: int = 100  # requests per minute
    status: DataSourceStatus = DataSourceStatus.ACTIVE
    supported_assets: List[AssetClass] = None

class BaseAssetAdapter:
    """资产适配器基类"""

    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.session = None
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_window = 60  # seconds

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers=self._get_headers()
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "User-Agent": "Multi-Asset-Quant-System/1.0",
            "Content-Type": "application/json"
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    async def _check_rate_limit(self):
        """检查速率限制"""
        current_time = time.time()
        if current_time - self.last_request_time >= self.rate_limit_window:
            self.request_count = 0
            self.last_request_time = current_time

        if self.request_count >= self.config.rate_limit:
            wait_time = self.rate_limit_window - (current_time - self.last_request_time)
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)

        self.request_count += 1

    async def _make_request(self, url: str, params: Dict = None) -> Dict:
        """发起HTTP请求"""
        await self._check_rate_limit()

        for attempt in range(self.config.max_retries):
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"HTTP {response.status}: {url}")
                        if attempt == self.config.max_retries - 1:
                            raise Exception(f"Failed after {self.config.max_retries} attempts")

            except Exception as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                else:
                    raise

    def normalize_data(self, raw_data: Dict, symbol: str) -> MarketData:
        """标准化数据格式 - 子类必须实现"""
        raise NotImplementedError

    async def get_market_data(
        self,
        symbol: str,
        timeframe: Timeframe = Timeframe.TICK_1H,
        limit: int = 1000
    ) -> List[MarketData]:
        """获取市场数据 - 子类必须实现"""
        raise NotImplementedError

class ForexAdapter(BaseAssetAdapter):
    """外汇数据适配器"""

    def __init__(self):
        # 使用免费的外汇API (如Yahoo Finance)
        config = DataSourceConfig(
            name="Yahoo_Finance_Forex",
            url="https://query1.finance.yahoo.com/v8/finance/chart",
            supported_assets=[AssetClass.FOREX]
        )
        super().__init__(config)

    async def get_forex_pairs(self) -> List[str]:
        """获取支持的外汇对列表"""
        return [
            "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X",
            "AUDUSD=X", "USDCAD=X", "NZDUSD=X",
            "EURGBP=X", "EURJPY=X", "GBPJPY=X"
        ]

    async def get_market_data(
        self,
        symbol: str,
        timeframe: Timeframe = Timeframe.TICK_1H,
        limit: int = 1000
    ) -> List[MarketData]:
        """获取外汇数据"""
        # Yahoo Finance外汇符号格式
        yahoo_symbol = f"{symbol}=X" if not symbol.endswith("=X") else symbol

        # 计算时间范围
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=limit // 24)  # 假设1小时数据

        params = {
            "symbol": yahoo_symbol,
            "period1": int(start_time.timestamp()),
            "period2": int(end_time.timestamp()),
            "interval": self._convert_timeframe(timeframe)
        }

        try:
            data = await self._make_request(self.config.url, params)
            return self._normalize_yahoo_forex_data(data, symbol)

        except Exception as e:
            logger.error(f"Failed to get forex data for {symbol}: {e}")
            return []

    def _convert_timeframe(self, timeframe: Timeframe) -> str:
        """转换时间周期到Yahoo Finance格式"""
        mapping = {
            Timeframe.TICK_1M: "1m",
            Timeframe.TICK_5M: "5m",
            Timeframe.TICK_15M: "15m",
            Timeframe.TICK_30M: "30m",
            Timeframe.TICK_1H: "1h",
            Timeframe.TICK_1D: "1d",
            Timeframe.TICK_1W: "1wk"
        }
        return mapping.get(timeframe, "1h")

    def _normalize_yahoo_forex_data(self, raw_data: Dict, symbol: str) -> List[MarketData]:
        """标准化Yahoo Finance外汇数据"""
        try:
            result = raw_data.get("chart", {}).get("result", [])
            if not result:
                return []

            chart_data = result[0]
            timestamps = chart_data.get("timestamp", [])
            ohlc = chart_data.get("indicators", {}).get("quote", [{}])[0]

            if not timestamps or not ohlc:
                return []

            market_data_list = []

            for i, timestamp in enumerate(timestamps):
                try:
                    market_data = MarketData(
                        symbol=symbol,
                        asset_class=AssetClass.FOREX,
                        exchange=Exchange.FOREX_MARKET,
                        region=MarketRegion.GLOBAL,
                        timestamp=datetime.fromtimestamp(timestamp),
                        timeframe=Timeframe.TICK_1H,
                        open=float(ohlc["open"][i]) if ohlc["open"][i] else 0,
                        high=float(ohlc["high"][i]) if ohlc["high"][i] else 0,
                        low=float(ohlc["low"][i]) if ohlc["low"][i] else 0,
                        close=float(ohlc["close"][i]) if ohlc["close"][i] else 0,
                        volume=float(ohlc["volume"][i]) if ohlc.get("volume") and ohlc["volume"][i] else 0
                    )
                    market_data_list.append(market_data)
                except (IndexError, TypeError, ValueError) as e:
                    logger.warning(f"Skipping invalid data point at index {i}: {e}")
                    continue

            return market_data_list

        except Exception as e:
            logger.error(f"Failed to normalize forex data: {e}")
            return []

class CryptoAdapter(BaseAssetAdapter):
    """加密货币数据适配器"""

    def __init__(self):
        # 使用Binance公开API
        config = DataSourceConfig(
            name="Binance_API",
            url="https://api.binance.com/api/v3",
            supported_assets=[AssetClass.CRYPTO]
        )
        super().__init__(config)

    async def get_crypto_symbols(self) -> List[str]:
        """获取支持的加密货币列表"""
        try:
            data = await self._make_request(f"{self.config.url}/exchangeInfo")
            symbols = [s["symbol"] for s in data["symbols"] if s["status"] == "TRADING"]
            return [s for s in symbols if s.endswith("USDT") or s.endswith("USD")]
        except Exception as e:
            logger.error(f"Failed to get crypto symbols: {e}")
            return ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

    async def get_market_data(
        self,
        symbol: str,
        timeframe: Timeframe = Timeframe.TICK_1H,
        limit: int = 1000
    ) -> List[MarketData]:
        """获取加密货币数据"""
        # Binance需要符号格式转换
        binance_symbol = self._convert_symbol_to_binance(symbol)

        interval = self._convert_timeframe(timeframe)
        params = {
            "symbol": binance_symbol,
            "interval": interval,
            "limit": min(limit, 1000)  # Binance max 1000
        }

        try:
            data = await self._make_request(f"{self.config.url}/klines", params)
            return self._normalize_binance_crypto_data(data, symbol)

        except Exception as e:
            logger.error(f"Failed to get crypto data for {symbol}: {e}")
            return []

    def _convert_symbol_to_binance(self, symbol: str) -> str:
        """转换符号到Binance格式"""
        if symbol.endswith("USD"):
            return symbol.replace("USD", "USDT")
        elif symbol.endswith("USDT"):
            return symbol
        else:
            return f"{symbol}USDT"

    def _convert_timeframe(self, timeframe: Timeframe) -> str:
        """转换时间周期到Binance格式"""
        mapping = {
            Timeframe.TICK_1M: "1m",
            Timeframe.TICK_5M: "5m",
            Timeframe.TICK_15M: "15m",
            Timeframe.TICK_30M: "30m",
            Timeframe.TICK_1H: "1h",
            Timeframe.TICK_4H: "4h",
            Timeframe.TICK_1D: "1d",
            Timeframe.TICK_1W: "1w"
        }
        return mapping.get(timeframe, "1h")

    def _normalize_binance_crypto_data(self, raw_data: List, symbol: str) -> List[MarketData]:
        """标准化Binance加密货币数据"""
        market_data_list = []

        for kline in raw_data:
            try:
                # Binance kline format: [open_time, open, high, low, close, volume, close_time, ...]
                market_data = MarketData(
                    symbol=symbol,
                    asset_class=AssetClass.CRYPTO,
                    exchange=Exchange.BINANCE,
                    region=MarketRegion.GLOBAL,
                    timestamp=datetime.fromtimestamp(int(kline[0]) / 1000),
                    timeframe=Timeframe.TICK_1H,
                    open=float(kline[1]),
                    high=float(kline[2]),
                    low=float(kline[3]),
                    close=float(kline[4]),
                    volume=float(kline[5])
                )
                market_data_list.append(market_data)
            except (IndexError, ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid kline data: {e}")
                continue

        return market_data_list

class CommodityAdapter(BaseAssetAdapter):
    """大宗商品数据适配器"""

    def __init__(self):
        # 使用Yahoo Finance商品ETF数据
        config = DataSourceConfig(
            name="Yahoo_Finance_Commodities",
            url="https://query1.finance.yahoo.com/v8/finance/chart",
            supported_assets=[AssetClass.COMMODITY]
        )
        super().__init__(config)

    async def get_commodity_symbols(self) -> Dict[str, str]:
        """获取商品符号映射"""
        return {
            "XAUUSD": "GC=F",      # 黄金期货
            "XAGUSD": "SI=F",      # 白银期货
            "CLUSD": "CL=F",       # 原油期货
            "NGUSD": "NG=F",       # 天然气期货
            "HGUSD": "HG=F",       # 铜期货
            "ZCUSD": "ZC=F",       # 玉米期货
            "ZWUSD": "ZW=F",       # 小麦期货
        }

    async def get_market_data(
        self,
        symbol: str,
        timeframe: Timeframe = Timeframe.TICK_1H,
        limit: int = 1000
    ) -> List[MarketData]:
        """获取商品数据"""
        symbol_map = await self.get_commodity_symbols()
        yahoo_symbol = symbol_map.get(symbol, symbol)

        # 计算时间范围
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=limit // 24)

        params = {
            "symbol": yahoo_symbol,
            "period1": int(start_time.timestamp()),
            "period2": int(end_time.timestamp()),
            "interval": self._convert_timeframe(timeframe)
        }

        try:
            data = await self._make_request(self.config.url, params)
            return self._normalize_yahoo_commodity_data(data, symbol)

        except Exception as e:
            logger.error(f"Failed to get commodity data for {symbol}: {e}")
            return []

    def _convert_timeframe(self, timeframe: Timeframe) -> str:
        """转换时间周期到Yahoo Finance格式"""
        mapping = {
            Timeframe.TICK_1M: "1m",
            Timeframe.TICK_5M: "5m",
            Timeframe.TICK_15M: "15m",
            Timeframe.TICK_30M: "30m",
            Timeframe.TICK_1H: "1h",
            Timeframe.TICK_1D: "1d",
            Timeframe.TICK_1W: "1wk"
        }
        return mapping.get(timeframe, "1h")

    def _normalize_yahoo_commodity_data(self, raw_data: Dict, symbol: str) -> List[MarketData]:
        """标准化Yahoo Finance商品数据"""
        try:
            result = raw_data.get("chart", {}).get("result", [])
            if not result:
                return []

            chart_data = result[0]
            timestamps = chart_data.get("timestamp", [])
            ohlc = chart_data.get("indicators", {}).get("quote", [{}])[0]

            if not timestamps or not ohlc:
                return []

            market_data_list = []

            for i, timestamp in enumerate(timestamps):
                try:
                    market_data = MarketData(
                        symbol=symbol,
                        asset_class=AssetClass.COMMODITY,
                        exchange=Exchange.CME,
                        region=MarketRegion.GLOBAL,
                        timestamp=datetime.fromtimestamp(timestamp),
                        timeframe=Timeframe.TICK_1H,
                        open=float(ohlc["open"][i]) if ohlc["open"][i] else 0,
                        high=float(ohlc["high"][i]) if ohlc["high"][i] else 0,
                        low=float(ohlc["low"][i]) if ohlc["low"][i] else 0,
                        close=float(ohlc["close"][i]) if ohlc["close"][i] else 0,
                        volume=float(ohlc["volume"][i]) if ohlc.get("volume") and ohlc["volume"][i] else 0
                    )
                    market_data_list.append(market_data)
                except (IndexError, TypeError, ValueError) as e:
                    logger.warning(f"Skipping invalid commodity data point at index {i}: {e}")
                    continue

            return market_data_list

        except Exception as e:
            logger.error(f"Failed to normalize commodity data: {e}")
            return []

class MultiAssetDataAdapter:
    """多资产数据适配器管理器"""

    def __init__(self):
        self.adapters = {
            AssetClass.FOREX: ForexAdapter(),
            AssetClass.CRYPTO: CryptoAdapter(),
            AssetClass.COMMODITY: CommodityAdapter()
        }
        self.cache = {}  # 简单内存缓存
        self.cache_ttl = 300  # 5分钟缓存

    async def initialize(self):
        """初始化所有适配器"""
        for adapter in self.adapters.values():
            # 这里可以添加连接测试等初始化逻辑
            logger.info(f"Initialized {adapter.__class__.__name__}")

    async def get_market_data(
        self,
        symbol: str,
        timeframe: Timeframe = Timeframe.TICK_1H,
        limit: int = 1000,
        use_cache: bool = True
    ) -> List[MarketData]:
        """统一的市场数据获取接口"""
        # 解析符号
        asset_info = parse_symbol(symbol)
        asset_class = asset_info["asset_class"]

        # 检查缓存
        cache_key = f"{symbol}_{timeframe.value}_{limit}"
        if use_cache and cache_key in self.cache:
            cached_data, cache_time = self.cache[cache_key]
            if time.time() - cache_time < self.cache_ttl:
                logger.debug(f"Using cached data for {symbol}")
                return cached_data

        # 获取对应的适配器
        adapter = self.adapters.get(asset_class)
        if not adapter:
            logger.error(f"No adapter found for asset class {asset_class}")
            return []

        try:
            async with adapter:
                data = await adapter.get_market_data(symbol, timeframe, limit)

                # 缓存结果
                if use_cache and data:
                    self.cache[cache_key] = (data, time.time())

                logger.info(f"Retrieved {len(data)} data points for {symbol}")
                return data

        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            return []

    async def get_multiple_market_data(
        self,
        symbols: List[str],
        timeframe: Timeframe = Timeframe.TICK_1H,
        limit: int = 1000
    ) -> Dict[str, List[MarketData]]:
        """批量获取多个资产的市场数据"""
        tasks = {}
        for symbol in symbols:
            task = asyncio.create_task(
                self.get_market_data(symbol, timeframe, limit)
            )
            tasks[symbol] = task

        results = {}
        for symbol, task in tasks.items():
            try:
                results[symbol] = await task
            except Exception as e:
                logger.error(f"Failed to get data for {symbol}: {e}")
                results[symbol] = []

        return results

    def to_dataframe(self, market_data_list: List[MarketData]) -> pd.DataFrame:
        """转换为DataFrame"""
        if not market_data_list:
            return pd.DataFrame()

        data = []
        for md in market_data_list:
            row = {
                'timestamp': md.timestamp,
                'symbol': md.symbol,
                'open': md.open,
                'high': md.high,
                'low': md.low,
                'close': md.close,
                'volume': md.volume,
                'asset_class': md.asset_class.value,
                'exchange': md.exchange.value
            }

            # 添加可选字段
            if md.bid is not None:
                row['bid'] = md.bid
            if md.ask is not None:
                row['ask'] = md.ask
            if md.spread is not None:
                row['spread'] = md.spread

            data.append(row)

        return pd.DataFrame(data).set_index('timestamp')

    def clear_cache(self):
        """清除缓存"""
        self.cache.clear()
        logger.info("Cache cleared")

    async def test_connection(self) -> Dict[str, bool]:
        """测试所有数据源连接"""
        test_symbols = {
            AssetClass.FOREX: "EURUSD",
            AssetClass.CRYPTO: "BTCUSD",
            AssetClass.COMMODITY: "XAUUSD"
        }

        results = {}
        for asset_class, symbol in test_symbols.items():
            try:
                data = await self.get_market_data(symbol, limit=10)
                results[asset_class.value] = len(data) > 0
            except Exception as e:
                logger.error(f"Connection test failed for {asset_class}: {e}")
                results[asset_class.value] = False

        return results

# 使用示例
async def main():
    """测试多资产数据适配器"""
    adapter = MultiAssetDataAdapter()
    await adapter.initialize()

    # 测试连接
    connection_results = await adapter.test_connection()
    print("Connection test results:", connection_results)

    # 获取不同资产的数据
    symbols = ["EURUSD", "BTCUSD", "XAUUSD"]
    data = await adapter.get_multiple_market_data(symbols, limit=100)

    for symbol, market_data in data.items():
        if market_data:
            df = adapter.to_dataframe(market_data)
            print(f"\n{symbol} data:")
            print(f"Shape: {df.shape}")
            print(f"Latest price: {df['close'].iloc[-1]:.4f}")
            print(f"Data range: {df.index.min()} to {df.index.max()}")

if __name__ == "__main__":
    asyncio.run(main())
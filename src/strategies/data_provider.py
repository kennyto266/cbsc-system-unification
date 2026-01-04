"""
Strategy Data Provider
策略數據提供者

統一的數據接口，支持：
- 實時市場數據
- 歷史數據
- 多數據源整合
- 數據預處理
- 緩存機制
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import asyncio
import aiohttp
import logging
from dataclasses import dataclass
import sqlite3
import os
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger('DataProvider')

@dataclass
class MarketData:
    """市場數據結構"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    adj_close: Optional[float] = None
    turnover: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None

@dataclass
class DataRequest:
    """數據請求參數"""
    symbols: Union[str, List[str]]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    timeframe: str = '1d'  # 1m, 5m, 15m, 1h, 1d, 1w, 1M
    fields: List[str] = None  # ['open', 'high', 'low', 'close', 'volume']
    limit: Optional[int] = None

class DataSourceBase(ABC):
    """數據源基類"""

    @abstractmethod
    async def get_market_data(self, request: DataRequest) -> pd.DataFrame:
        """獲取市場數據"""
        pass

    @abstractmethod
    async def get_real_time_price(self, symbol: str) -> MarketData:
        """獲取實時價格"""
        pass

class FutuDataSource(DataSourceBase):
    """富途數據源"""

    def __init__(self, host='127.0.0.1', port=11111):
        self.host = host
        self.port = port
        self.is_connected = False

    async def connect(self):
        """連接富途OpenD"""
        # 這裡應該實現實際的富途連接邏輯
        # 為了演示，使用模擬數據
        self.is_connected = True
        logger.info(f"已連接富途OpenD: {self.host}:{self.port}")

    async def get_market_data(self, request: DataRequest) -> pd.DataFrame:
        """從富途獲取歷史數據"""
        if not self.is_connected:
            await self.connect()

        # 模擬數據返回
        dates = pd.date_range(
            start=request.start_date or datetime.now() - timedelta(days=365),
            end=request.end_date or datetime.now(),
            freq='D'
        )

        if isinstance(request.symbols, str):
            symbols = [request.symbols]
        else:
            symbols = request.symbols

        data_dict = {}
        for symbol in symbols:
            # 生成模擬數據
            np.random.seed(hash(symbol) % 2**32)  # 確保每個標的數據一致性

            base_price = 100 + np.random.randn() * 20
            returns = np.random.normal(0.001, 0.02, len(dates))
            prices = base_price * np.exp(np.cumsum(returns))

            volumes = np.random.randint(1000000, 10000000, len(dates))

            # OHLC數據
            high_low_range = np.random.uniform(0.01, 0.05, len(dates))
            highs = prices * (1 + high_low_range / 2)
            lows = prices * (1 - high_low_range / 2)
            opens = np.roll(prices, 1)
            opens[0] = prices[0]

            for field in request.fields or ['open', 'high', 'low', 'close', 'volume']:
                data_dict[f'{field}_{symbol}'] = {
                    'open': opens,
                    'high': highs,
                    'low': lows,
                    'close': prices,
                    'volume': volumes
                }[field]

        df = pd.DataFrame(data_dict, index=dates)
        return df

    async def get_real_time_price(self, symbol: str) -> MarketData:
        """獲取實時價格"""
        # 模擬實時數據
        base_price = 100 + np.random.randn() * 20
        return MarketData(
            symbol=symbol,
            timestamp=datetime.now(),
            open=base_price * (1 + np.random.randn() * 0.01),
            high=base_price * (1 + abs(np.random.randn() * 0.02)),
            low=base_price * (1 - abs(np.random.randn() * 0.02)),
            close=base_price * (1 + np.random.randn() * 0.01),
            volume=np.random.randint(100000, 1000000)
        )

class YahooFinanceDataSource(DataSourceBase):
    """Yahoo Finance數據源"""

    def __init__(self):
        self.session = None

    async def _ensure_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def get_market_data(self, request: DataRequest) -> pd.DataFrame:
        """從Yahoo Finance獲取數據"""
        await self._ensure_session()

        # 這裡應該實現實際的Yahoo Finance API調用
        # 為了演示，返回模擬數據
        return await self._generate_mock_data(request)

    async def _generate_mock_data(self, request: DataRequest) -> pd.DataFrame:
        """生成模擬數據"""
        dates = pd.date_range(
            start=request.start_date or datetime.now() - timedelta(days=365),
            end=request.end_date or datetime.now(),
            freq='D'
        )

        if isinstance(request.symbols, str):
            symbols = [request.symbols]
        else:
            symbols = request.symbols

        data_dict = {}
        for symbol in symbols:
            # 為每個標的生成獨特的模擬數據
            np.random.seed(hash(symbol) % 2**32)
            base_price = 50 + np.random.randn() * 30
            prices = base_price * np.exp(np.cumsum(np.random.normal(0.0005, 0.02, len(dates))))
            volumes = np.random.randint(500000, 5000000, len(dates))

            for field in request.fields or ['close']:
                if field == 'close':
                    data_dict[f'close_{symbol}'] = prices
                elif field == 'volume':
                    data_dict[f'volume_{symbol}'] = volumes

        df = pd.DataFrame(data_dict, index=dates)
        return df

    async def get_real_time_price(self, symbol: str) -> MarketData:
        """獲取實時價格"""
        await self._ensure_session()
        # 模擬實時數據
        return MarketData(
            symbol=symbol,
            timestamp=datetime.now(),
            open=0,
            high=0,
            low=0,
            close=np.random.uniform(50, 200),
            volume=0
        )

class CacheManager:
    """緩存管理器"""

    def __init__(self, cache_dir: str = 'cache'):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.memory_cache: Dict[str, Tuple[pd.DataFrame, datetime]] = {}
        self.cache_ttl = timedelta(minutes=15)  # 緩存15分鐘

    def _get_cache_key(self, request: DataRequest) -> str:
        """生成緩存鍵"""
        return f"{str(request.symbols)}_{request.start_date}_{request.end_date}_{request.timeframe}"

    def get(self, request: DataRequest) -> Optional[pd.DataFrame]:
        """獲取緩存數據"""
        cache_key = self._get_cache_key(request)

        # 檢查內存緩存
        if cache_key in self.memory_cache:
            data, timestamp = self.memory_cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                return data.copy()
            else:
                del self.memory_cache[cache_key]

        # 檢查磁盤緩存
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.parquet")
        if os.path.exists(cache_file):
            file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - file_time < self.cache_ttl:
                df = pd.read_parquet(cache_file)
                self.memory_cache[cache_key] = (df, datetime.now())
                return df.copy()

        return None

    def set(self, request: DataRequest, data: pd.DataFrame):
        """設置緩存"""
        cache_key = self._get_cache_key(request)

        # 保存到內存緩存
        self.memory_cache[cache_key] = (data.copy(), datetime.now())

        # 保存到磁盤緩存
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.parquet")
        data.to_parquet(cache_file)

class DataProvider:
    """統一的數據提供者"""

    def __init__(self):
        self.data_sources: Dict[str, DataSourceBase] = {}
        self.cache_manager = CacheManager()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.default_source = 'futu'

        # 註冊默認數據源
        self.register_source('futu', FutuDataSource())
        self.register_source('yahoo', YahooFinanceDataSource())

    def register_source(self, name: str, source: DataSourceBase):
        """註冊數據源"""
        self.data_sources[name] = source
        logger.info(f"已註冊數據源: {name}")

    async def get_market_data(
        self,
        symbols: Union[str, List[str]],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        timeframe: str = '1d',
        fields: List[str] = None,
        source: Optional[str] = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """獲取市場數據"""

        request = DataRequest(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
            fields=fields or ['open', 'high', 'low', 'close', 'volume']
        )

        # 嘗試從緩存獲取
        if use_cache:
            cached_data = self.cache_manager.get(request)
            if cached_data is not None:
                logger.debug(f"從緩存獲取數據: {symbols}")
                return cached_data

        # 從數據源獲取
        source_name = source or self.default_source
        if source_name not in self.data_sources:
            raise ValueError(f"未知的數據源: {source_name}")

        logger.info(f"從數據源 {source_name} 獲取數據: {symbols}")
        data = await self.data_sources[source_name].get_market_data(request)

        # 保存到緩存
        if use_cache:
            self.cache_manager.set(request, data)

        return data

    async def get_real_time_price(
        self,
        symbol: str,
        source: Optional[str] = None
    ) -> MarketData:
        """獲取實時價格"""
        source_name = source or self.default_source
        if source_name not in self.data_sources:
            raise ValueError(f"未知的數據源: {source_name}")

        return await self.data_sources[source_name].get_real_time_price(symbol)

    def get_market_data_sync(
        self,
        symbols: Union[str, List[str]],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        timeframe: str = '1d',
        fields: List[str] = None,
        source: Optional[str] = None
    ) -> pd.DataFrame:
        """同步獲取市場數據"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.get_market_data(symbols, start_date, end_date, timeframe, fields, source)
            )
        finally:
            loop.close()

    async def stream_real_time_data(
        self,
        symbols: List[str],
        callback,
        interval: float = 1.0
    ):
        """實時數據流"""
        logger.info(f"開始實時數據流: {symbols}")

        while True:
            try:
                tasks = []
                for symbol in symbols:
                    task = self.get_real_time_price(symbol)
                    tasks.append(task)

                prices = await asyncio.gather(*tasks)
                await callback(prices)

                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"實時數據流出錯: {str(e)}")
                await asyncio.sleep(5)  # 錯誤後等待5秒

    def prepare_data_for_strategy(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        timeframe: str = '1d'
    ) -> pd.DataFrame:
        """為策略準備數據格式"""
        data = self.get_market_data_sync(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
            fields=['open', 'high', 'low', 'close', 'volume']
        )

        # 確保數據格式正確
        if data.empty:
            logger.warning(f"未獲取到數據: {symbols}")
            return pd.DataFrame()

        # 填充缺失值
        data = data.fillna(method='ffill').fillna(method='bfill')

        return data

    def validate_data(self, data: pd.DataFrame) -> bool:
        """驗證數據質量"""
        if data.empty:
            logger.error("數據為空")
            return False

        # 檢查是否有缺失值
        if data.isnull().any().any():
            logger.warning("數據存在缺失值")
            # 嘗試填充
            data.fillna(method='ffill', inplace=True)
            data.fillna(method='bfill', inplace=True)

        # 檢查數據範圍
        for col in data.columns:
            if 'close_' in col or 'open_' in col or 'high_' in col or 'low_' in col:
                if (data[col] <= 0).any():
                    logger.error(f"數據異常: {col} 包含非正值")
                    return False

        return True

    async def close(self):
        """關閉數據提供者"""
        # 關閉所有數據源連接
        for source in self.data_sources.values():
            if hasattr(source, 'session') and source.session:
                await source.session.close()

        # 關閉線程池
        self.executor.shutdown(wait=True)

# 全局數據提供者實例
_data_provider_instance: Optional[DataProvider] = None

def get_data_provider() -> DataProvider:
    """獲取全局數據提供者實例"""
    global _data_provider_instance
    if _data_provider_instance is None:
        _data_provider_instance = DataProvider()
    return _data_provider_instance

async def fetch_data_for_strategy(
    strategy_config,
    days_back: int = 365
) -> pd.DataFrame:
    """為策略配置獲取數據的便捷函數"""
    data_provider = get_data_provider()

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    return await data_provider.get_market_data(
        symbols=strategy_config.symbols,
        start_date=start_date,
        end_date=end_date,
        timeframe=strategy_config.timeframe
    )
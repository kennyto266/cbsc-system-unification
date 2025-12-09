"""
Alpha Vantage 數據適配器 - 專業金融數據源

提供高質量的股票、外匯、加密貨幣數據
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import aiohttp
import pandas as pd

from .base_adapter import (
    BaseDataAdapter,
    DataAdapterConfig,
    DataQuality,
    DataSourceType,
    DataValidationResult,
    RealMarketData,
)


class AlphaVantageAdapter(BaseDataAdapter):
    """Alpha Vantage 數據適配器"""

    def __init__(self, config: DataAdapterConfig):
        config.source_type = DataSourceType.ALPHA_VANTAGE
        super().__init__(config)
        self.logger = logging.getLogger("hk_quant_system.alpha_vantage")
        self.api_key = config.config.get("api_key")
        self.base_url = "https://www.alphavantage.co / query"
        self._session = None

        if not self.api_key:
            self.logger.warning("No API key provided for Alpha Vantage")

    async def connect(self) -> bool:
        """連接到Alpha Vantage"""
        try:
            if not self.api_key:
                self.logger.error("No API key provided")
                return False

            self.logger.info("Connecting to Alpha Vantage...")

            # 測試連接
            async with aiohttp.ClientSession() as session:
                params = {
                    "function": "TIME_SERIES_INTRADAY",
                    "symbol": "AAPL",
                    "interval": "1min",
                    "apikey": self.api_key,
                }

                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "Error Message" not in data and "Note" not in data:
                            self.logger.info("Successfully connected to Alpha Vantage")
                            return True
                        else:
                            self.logger.error(
                                f"API Error: {data.get('Error Message', data.get('Note', 'Unknown error'))}"
                            )
                            return False
                    else:
                        self.logger.error(f"HTTP Error: {response.status}")
                        return False

        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False

    async def disconnect(self) -> bool:
        """斷開連接"""
        try:
            if self._session:
                await self._session.close()
                self._session = None
            return True
        except Exception as e:
            self.logger.error(f"Disconnection error: {e}")
            return False

    async def get_market_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[RealMarketData]:
        """獲取市場數據"""
        try:
            # 檢查緩存
            cache_key = self.get_cache_key(symbol, start_date, end_date)
            cached_data = self.get_cache(cache_key)
            if cached_data:
                self.logger.debug(f"Using cached data for {symbol}")
                return cached_data

            self.logger.info(f"Fetching market data for {symbol}")

            # 獲取日線數據
            daily_data = await self._get_daily_data(symbol)
            if not daily_data:
                return []

            # 轉換為標準格式
            market_data = await self.transform_data(daily_data, symbol)

            # 驗證數據質量
            validation_result = await self.validate_data(market_data)
            if validation_result.quality_level in [
                DataQuality.POOR,
                DataQuality.UNKNOWN,
            ]:
                self.logger.warning(
                    f"Poor data quality for {symbol}: {validation_result.errors}"
                )

            # 緩存數據
            self.set_cache(cache_key, market_data)

            self.logger.info(
                f"Successfully fetched {len(market_data)} data points for {symbol}"
            )
            return market_data

        except Exception as e:
            self.logger.error(f"Error fetching market data for {symbol}: {e}")
            return []

    async def _get_daily_data(self, symbol: str) -> Optional[Dict]:
        """獲取日線數據"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "function": "TIME_SERIES_DAILY",
                    "symbol": symbol,
                    "outputsize": "full",
                    "apikey": self.api_key,
                }

                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if "Error Message" in data:
                            self.logger.error(f"API Error: {data['Error Message']}")
                            return None

                        if "Note" in data:
                            self.logger.warning(f"API Note: {data['Note']}")
                            return None

                        if "Time Series (Daily)" in data:
                            return data["Time Series (Daily)"]
                        else:
                            self.logger.error(f"No time series data found for {symbol}")
                            return None
                    else:
                        self.logger.error(f"HTTP Error: {response.status}")
                        return None

        except Exception as e:
            self.logger.error(f"Error fetching daily data for {symbol}: {e}")
            return None

    async def transform_data(self, raw_data: Dict, symbol: str) -> List[RealMarketData]:
        """轉換原始數據為標準格式"""
        try:
            market_data = []

            for date_str, values in raw_data.items():
                try:
                    # 解析日期
                    timestamp = datetime.strptime(date_str, "%Y-%m-%d")

                    data_point = RealMarketData(
                        symbol=symbol,
                        timestamp=timestamp,
                        open_price=Decimal(str(values["1. open"])),
                        high_price=Decimal(str(values["2. high"])),
                        low_price=Decimal(str(values["3. low"])),
                        close_price=Decimal(str(values["4. close"])),
                        volume=int(values["5. volume"]),
                        market_cap=None,  # Alpha Vantage 不提供市值
                        pe_ratio=None,  # Alpha Vantage 不提供PE比率
                        data_source="alpha_vantage",
                        quality_score=0.95,  # Alpha Vantage 數據質量很高
                        last_updated=datetime.now(),
                    )
                    market_data.append(data_point)

                except (ValueError, KeyError) as e:
                    self.logger.warning(f"Error parsing data for {date_str}: {e}")
                    continue

            # 按時間排序
            market_data.sort(key=lambda x: x.timestamp)

            return market_data

        except Exception as e:
            self.logger.error(f"Error transforming data: {e}")
            return []

    async def validate_data(self, data: List[RealMarketData]) -> DataValidationResult:
        """驗證數據質量"""
        try:
            if not data:
                return DataValidationResult(
                    is_valid=False,
                    quality_score=0.0,
                    quality_level=DataQuality.POOR,
                    errors=["No data provided"],
                    warnings=[],
                )

            errors = []
            warnings = []

            # 檢查數據完整性
            for i, item in enumerate(data):
                # 檢查價格數據
                if (
                    item.open_price <= 0
                    or item.high_price <= 0
                    or item.low_price <= 0
                    or item.close_price <= 0
                ):
                    errors.append(f"Invalid price data at index {i}")

                # 檢查價格邏輯
                if item.high_price < item.low_price:
                    errors.append(f"High price < Low price at index {i}")

                if (
                    item.high_price < item.open_price
                    or item.high_price < item.close_price
                ):
                    errors.append(f"High price not highest at index {i}")

                if (
                    item.low_price > item.open_price
                    or item.low_price > item.close_price
                ):
                    errors.append(f"Low price not lowest at index {i}")

                # 檢查成交量
                if item.volume < 0:
                    errors.append(f"Negative volume at index {i}")

            # 計算質量評分
            quality_score = self.calculate_quality_score(data)
            quality_level = self.get_quality_level(quality_score)

            # 檢查數據連續性
            if len(data) > 1:
                for i in range(1, len(data)):
                    gap = (data[i].timestamp - data[i - 1].timestamp).days
                    if gap > 3:  # 超過3天的間隔（考慮週末）
                        warnings.append(
                            f"Large time gap: {gap} days between {data[i - 1].timestamp} and {data[i].timestamp}"
                        )

            is_valid = (
                len(errors) == 0 and quality_score >= self.config.quality_threshold
            )

            return DataValidationResult(
                is_valid=is_valid,
                quality_score=quality_score,
                quality_level=quality_level,
                errors=errors,
                warnings=warnings,
                metadata={
                    "data_points": len(data),
                    "symbol": data[0].symbol if data else None,
                    "date_range": {
                        "start": data[0].timestamp if data else None,
                        "end": data[-1].timestamp if data else None,
                    },
                },
            )

        except Exception as e:
            self.logger.error(f"Error validating data: {e}")
            return DataValidationResult(
                is_valid=False,
                quality_score=0.0,
                quality_level=DataQuality.UNKNOWN,
                errors=[f"Validation error: {str(e)}"],
                warnings=[],
            )

    async def get_real_time_data(self, symbol: str) -> Optional[RealMarketData]:
        """獲取實時數據"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "function": "GLOBAL_QUOTE",
                    "symbol": symbol,
                    "apikey": self.api_key,
                }

                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if "Error Message" in data:
                            self.logger.error(f"API Error: {data['Error Message']}")
                            return None

                        if "Global Quote" in data:
                            quote = data["Global Quote"]

                            data_point = RealMarketData(
                                symbol=symbol,
                                timestamp=datetime.now(),
                                open_price=Decimal(str(quote["02. open"])),
                                high_price=Decimal(str(quote["03. high"])),
                                low_price=Decimal(str(quote["04. low"])),
                                close_price=Decimal(str(quote["05. price"])),
                                volume=int(quote["06. volume"]),
                                market_cap=None,
                                pe_ratio=None,
                                data_source="alpha_vantage_realtime",
                                quality_score=0.9,
                                last_updated=datetime.now(),
                            )

                            return data_point
                        else:
                            self.logger.error(f"No quote data found for {symbol}")
                            return None
                    else:
                        self.logger.error(f"HTTP Error: {response.status}")
                        return None

        except Exception as e:
            self.logger.error(f"Error fetching real - time data for {symbol}: {e}")
            return None

    async def get_technical_indicators(
        self,
        symbol: str,
        function: str = "SMA",
        interval: str = "daily",
        time_period: int = 20,
    ) -> Optional[Dict]:
        """獲取技術指標"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "function": function,
                    "symbol": symbol,
                    "interval": interval,
                    "time_period": time_period,
                    "series_type": "close",
                    "apikey": self.api_key,
                }

                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if "Error Message" in data:
                            self.logger.error(f"API Error: {data['Error Message']}")
                            return None

                        if "Note" in data:
                            self.logger.warning(f"API Note: {data['Note']}")
                            return None

                        return data
                    else:
                        self.logger.error(f"HTTP Error: {response.status}")
                        return None

        except Exception as e:
            self.logger.error(f"Error fetching technical indicators for {symbol}: {e}")
            return None

    async def get_company_overview(self, symbol: str) -> Optional[Dict]:
        """獲取公司概況"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "function": "OVERVIEW",
                    "symbol": symbol,
                    "apikey": self.api_key,
                }

                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if "Error Message" in data:
                            self.logger.error(f"API Error: {data['Error Message']}")
                            return None

                        return data
                    else:
                        self.logger.error(f"HTTP Error: {response.status}")
                        return None

        except Exception as e:
            self.logger.error(f"Error fetching company overview for {symbol}: {e}")
            return None

    async def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        """搜索標的符號"""
        try:
            # Alpha Vantage 沒有直接的搜索API
            # 這裡返回一些常見的標的
            common_symbols = {
                # 美股
                "AAPL": "Apple Inc.",
                "MSFT": "Microsoft Corporation",
                "GOOGL": "Alphabet Inc.",
                "AMZN": "Amazon.com Inc.",
                "TSLA": "Tesla Inc.",
                "META": "Meta Platforms Inc.",
                "NVDA": "NVIDIA Corporation",
                "JPM": "JPMorgan Chase & Co.",
                "JNJ": "Johnson & Johnson",
                "V": "Visa Inc.",
                # 港股 (需要特殊處理)
                "0700.HK": "騰訊控股",
                "0941.HK": "中國移動",
                "1299.HK": "友邦保險",
                "2800.HK": "盈富基金",
                "0388.HK": "香港交易所",
            }

            results = []
            query_lower = query.lower()

            for symbol, name in common_symbols.items():
                if query_lower in symbol.lower() or query_lower in name.lower():
                    results.append(
                        {
                            "symbol": symbol,
                            "name": name,
                            "exchange": (
                                "NASDAQ"
                                if symbol
                                in [
                                    "AAPL",
                                    "MSFT",
                                    "GOOGL",
                                    "AMZN",
                                    "TSLA",
                                    "META",
                                    "NVDA",
                                ]
                                else "NYSE" if symbol in ["JPM", "JNJ", "V"] else "HKEX"
                            ),
                        }
                    )

            return results

        except Exception as e:
            self.logger.error(f"Error searching symbols: {e}")
            return []

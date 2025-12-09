"""
CCXT 加密貨幣數據適配器 - 真實加密貨幣數據源

支持多個加密貨幣交易所的實時數據
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import ccxt
import pandas as pd

from .base_adapter import (
    BaseDataAdapter,
    DataAdapterConfig,
    DataQuality,
    DataSourceType,
    DataValidationResult,
    RealMarketData,
)


class CCXTCryptoAdapter(BaseDataAdapter):
    """CCXT 加密貨幣數據適配器"""

    def __init__(self, config: DataAdapterConfig):
        config.source_type = DataSourceType.CUSTOM  # CCXT 是自定義類型
        super().__init__(config)
        self.logger = logging.getLogger("hk_quant_system.ccxt_crypto")

        # 交易所配置
        self.exchange_name = config.config.get("exchange", "binance")
        self.sandbox = config.config.get("sandbox", True)  # 默認使用沙盒模式
        self.api_key = config.config.get("api_key")
        self.secret = config.config.get("secret")
        self.passphrase = config.config.get("passphrase")  # 某些交易所需要

        self.exchange = None

    async def connect(self) -> bool:
        """連接到加密貨幣交易所"""
        try:
            self.logger.info(f"Connecting to {self.exchange_name} exchange...")

            # 創建交易所實例
            exchange_class = getattr(ccxt, self.exchange_name)

            exchange_config = {
                "sandbox": self.sandbox,
                "enableRateLimit": True,
                "timeout": self.config.timeout * 1000,  # CCXT 使用毫秒
            }

            # 如果有API密鑰，添加認證信息
            if self.api_key and self.secret:
                exchange_config.update(
                    {
                        "apiKey": self.api_key,
                        "secret": self.secret,
                    }
                )

                if self.passphrase:
                    exchange_config["passphrase"] = self.passphrase

            self.exchange = exchange_class(exchange_config)

            # 測試連接
            if hasattr(self.exchange, "fetch_status"):
                status = await self._async_fetch_status()
                if status and status.get("status") == "ok":
                    self.logger.info(f"Successfully connected to {self.exchange_name}")
                    return True
                else:
                    self.logger.error(f"Exchange status error: {status}")
                    return False
            else:
                # 如果沒有狀態檢查，嘗試獲取市場數據
                markets = await self._async_fetch_markets()
                if markets:
                    self.logger.info(f"Successfully connected to {self.exchange_name}")
                    return True
                else:
                    self.logger.error("Failed to fetch markets")
                    return False

        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False

    async def _async_fetch_status(self) -> Optional[Dict]:
        """異步獲取交易所狀態"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.exchange.fetch_status)
        except Exception as e:
            self.logger.error(f"Error fetching status: {e}")
            return None

    async def _async_fetch_markets(self) -> Optional[Dict]:
        """異步獲取市場信息"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.exchange.fetch_markets)
        except Exception as e:
            self.logger.error(f"Error fetching markets: {e}")
            return None

    async def disconnect(self) -> bool:
        """斷開連接"""
        try:
            if self.exchange:
                # CCXT 交易所通常不需要顯式關閉
                self.exchange = None
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

            # 轉換時間為毫秒時間戳
            since = None
            if start_date:
                since = int(
                    datetime.combine(start_date, datetime.min.time()).timestamp() * 1000
                )

            # 獲取OHLCV數據
            ohlcv_data = await self._async_fetch_ohlcv(symbol, since=since)
            if not ohlcv_data:
                return []

            # 轉換為標準格式
            market_data = await self.transform_data(ohlcv_data, symbol)

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

    async def _async_fetch_ohlcv(
        self, symbol: str, since: Optional[int] = None
    ) -> Optional[List]:
        """異步獲取OHLCV數據"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, lambda: self.exchange.fetch_ohlcv(symbol, "1d", since=since)
            )
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV data for {symbol}: {e}")
            return None

    async def transform_data(self, raw_data: List, symbol: str) -> List[RealMarketData]:
        """轉換原始數據為標準格式"""
        try:
            market_data = []

            for ohlcv in raw_data:
                try:
                    # OHLCV格式: [timestamp, open, high, low, close, volume]
                    timestamp = datetime.fromtimestamp(ohlcv[0] / 1000)

                    data_point = RealMarketData(
                        symbol=symbol,
                        timestamp=timestamp,
                        open_price=Decimal(str(ohlcv[1])),
                        high_price=Decimal(str(ohlcv[2])),
                        low_price=Decimal(str(ohlcv[3])),
                        close_price=Decimal(str(ohlcv[4])),
                        volume=int(ohlcv[5]),
                        market_cap=None,  # 加密貨幣數據通常不包含市值
                        pe_ratio=None,  # 加密貨幣沒有PE比率
                        data_source=f"ccxt_{self.exchange_name}",
                        quality_score=0.95,  # CCXT 數據質量很高
                        last_updated=datetime.now(),
                    )
                    market_data.append(data_point)

                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Error parsing OHLCV data: {e}")
                    continue

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

                # 檢查時間戳
                if item.timestamp > datetime.now():
                    warnings.append(f"Future timestamp at index {i}")

            # 計算質量評分
            quality_score = self.calculate_quality_score(data)
            quality_level = self.get_quality_level(quality_score)

            # 檢查數據連續性
            if len(data) > 1:
                for i in range(1, len(data)):
                    gap = (data[i].timestamp - data[i - 1].timestamp).days
                    if gap > 1:  # 加密貨幣市場24 / 7運行，間隔不應超過1天
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
                    "exchange": self.exchange_name,
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
            ticker_data = await self._async_fetch_ticker(symbol)
            if not ticker_data:
                return None

            data_point = RealMarketData(
                symbol=symbol,
                timestamp=datetime.now(),
                open_price=Decimal(
                    str(ticker_data.get("open", ticker_data.get("last", 0)))
                ),
                high_price=Decimal(
                    str(ticker_data.get("high", ticker_data.get("last", 0)))
                ),
                low_price=Decimal(
                    str(ticker_data.get("low", ticker_data.get("last", 0)))
                ),
                close_price=Decimal(str(ticker_data.get("last", 0))),
                volume=int(ticker_data.get("baseVolume", 0)),
                market_cap=None,
                pe_ratio=None,
                data_source=f"ccxt_{self.exchange_name}_realtime",
                quality_score=0.9,
                last_updated=datetime.now(),
            )

            return data_point

        except Exception as e:
            self.logger.error(f"Error fetching real - time data for {symbol}: {e}")
            return None

    async def _async_fetch_ticker(self, symbol: str) -> Optional[Dict]:
        """異步獲取ticker數據"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, lambda: self.exchange.fetch_ticker(symbol)
            )
        except Exception as e:
            self.logger.error(f"Error fetching ticker for {symbol}: {e}")
            return None

    async def get_order_book(self, symbol: str, limit: int = 20) -> Optional[Dict]:
        """獲取訂單簿"""
        try:
            loop = asyncio.get_event_loop()
            order_book = await loop.run_in_executor(
                None, lambda: self.exchange.fetch_order_book(symbol, limit)
            )
            return order_book
        except Exception as e:
            self.logger.error(f"Error fetching order book for {symbol}: {e}")
            return None

    async def get_trades(self, symbol: str, limit: int = 50) -> Optional[List]:
        """獲取最近交易"""
        try:
            loop = asyncio.get_event_loop()
            trades = await loop.run_in_executor(
                None, lambda: self.exchange.fetch_trades(symbol, limit=limit)
            )
            return trades
        except Exception as e:
            self.logger.error(f"Error fetching trades for {symbol}: {e}")
            return None

    async def get_supported_symbols(self) -> List[str]:
        """獲取支持的交易對"""
        try:
            markets = await self._async_fetch_markets()
            if not markets:
                return []

            symbols = []
            for market in markets:
                if market.get("active", True):  # 只包含活躍的市場
                    symbols.append(market["symbol"])

            return symbols

        except Exception as e:
            self.logger.error(f"Error getting supported symbols: {e}")
            return []

    async def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        """搜索交易對"""
        try:
            symbols = await self.get_supported_symbols()
            query_lower = query.lower()

            results = []
            for symbol in symbols:
                if query_lower in symbol.lower():
                    # 解析交易對
                    base_quote = symbol.split("/")
                    if len(base_quote) == 2:
                        results.append(
                            {
                                "symbol": symbol,
                                "base": base_quote[0],
                                "quote": base_quote[1],
                                "exchange": self.exchange_name,
                            }
                        )

            return results[:20]  # 限制結果數量

        except Exception as e:
            self.logger.error(f"Error searching symbols: {e}")
            return []

    async def get_exchange_info(self) -> Dict[str, Any]:
        """獲取交易所信息"""
        try:
            if not self.exchange:
                return {}

            markets = await self._async_fetch_markets()

            info = {
                "name": self.exchange_name,
                "id": self.exchange.id,
                "countries": self.exchange.countries,
                "rateLimit": self.exchange.rateLimit,
                "has": self.exchange.has,
                "urls": self.exchange.urls,
                "version": self.exchange.version,
                "markets_count": len(markets) if markets else 0,
                "sandbox": self.sandbox,
            }

            return info

        except Exception as e:
            self.logger.error(f"Error getting exchange info: {e}")
            return {}

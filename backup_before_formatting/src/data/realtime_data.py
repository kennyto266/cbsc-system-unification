"""
實時數據集成模塊
支持多個數據源的實時股票數據獲取
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
import pandas as pd


class RealtimeDataConfig:
    """實時數據配置"""

    def __init__(self):
        # Yahoo Finance API 配置
        self.yahoo_base_url = "https://query1.finance.yahoo.com / v8 / finance / chart"

        # 富途 API 配置（如可用）
        self.futu_base_url = "https://openapi.futunn.com"

        # 本地 API 配置（現有的）
        self.local_base_url = "http://18.180.162.113:9191"

        # 請求配置
        self.timeout = 30
        self.retry_times = 3
        self.retry_delay = 1


class RealtimeDataService:
    """實時數據服務"""

    def __init__(self, config: Optional[RealtimeDataConfig] = None):
        self.config = config or RealtimeDataConfig()
        self.logger = logging.getLogger(__name__)

        # 數據緩存
        self.data_cache = {}
        self.cache_ttl = 60  # 1分鐘緩存

        # 統計信息
        self.stats = {
            "requests_made": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cache_hits": 0,
        }

    async def get_stock_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """獲取股票實時價格"""
        # 檢查緩存
        cache_key = f"price_{symbol}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            self.stats["cache_hits"] += 1
            return cached_data

        # 嘗試多個數據源
        price_data = None

        # 1. 嘗試本地 API
        price_data = await self._get_from_local_api(symbol)

        # 2. 如果本地失敗，嘗試 Yahoo Finance
        if not price_data:
            price_data = await self._get_from_yahoo_finance(symbol)

        # 3. 緩存結果
        if price_data:
            self._cache_data(cache_key, price_data)
            self.stats["successful_requests"] += 1
        else:
            self.stats["failed_requests"] += 1

        self.stats["requests_made"] += 1
        return price_data

    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """獲取多個股票的價格"""
        results = {}

        # 並發獲取多個股票數據
        tasks = [self.get_stock_price(symbol) for symbol in symbols]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for symbol, response in zip(symbols, responses):
            if isinstance(response, Exception):
                self.logger.error(f"獲取 {symbol} 價格失敗: {response}")
                results[symbol] = None
            else:
                results[symbol] = response

        return results

    async def get_market_overview(self, market: str = "HK") -> Optional[Dict[str, Any]]:
        """獲取市場概覽"""
        cache_key = f"overview_{market}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        overview_data = None

        if market == "HK":
            overview_data = await self._get_hk_market_overview()

        if overview_data:
            self._cache_data(cache_key, overview_data)

        return overview_data

    async def get_technical_indicators(
        self, symbol: str, period: str = "1d"
    ) -> Optional[Dict[str, Any]]:
        """獲取技術指標數據"""
        cache_key = f"indicators_{symbol}_{period}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        indicators_data = None

        # 從本地 API 獲取技術指標
        indicators_data = await self._get_indicators_from_local(symbol, period)

        if indicators_data:
            self._cache_data(cache_key, indicators_data)

        return indicators_data

    async def _get_from_local_api(self, symbol: str) -> Optional[Dict[str, Any]]:
        """從本地 API 獲取數據"""
        try:
            url = f"{self.config.local_base_url}/inst / getInst"
            params = {"symbol": symbol.lower(), "duration": 1}  # 獲取最新數據

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_price_data(data, symbol)
                    else:
                        self.logger.warning(f"本地 API 請求失敗: {response.status}")
                        return None

        except Exception as e:
            self.logger.error(f"從本地 API 獲取數據失敗: {e}")
            return None

    async def _get_from_yahoo_finance(self, symbol: str) -> Optional[Dict[str, Any]]:
        """從 Yahoo Finance 獲取數據"""
        try:
            # 轉換港股代碼格式
            yahoo_symbol = self._convert_to_yahoo_symbol(symbol)

            url = f"{self.config.yahoo_base_url}/{yahoo_symbol}"
            params = {"interval": "1m", "range": "1d"}

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_yahoo_data(data, symbol)
                    else:
                        self.logger.warning(
                            f"Yahoo Finance 請求失敗: {response.status}"
                        )
                        return None

        except Exception as e:
            self.logger.error(f"從 Yahoo Finance 獲取數據失敗: {e}")
            return None

    async def _get_hk_market_overview(self) -> Optional[Dict[str, Any]]:
        """獲取港股市場概覽"""
        try:
            # 主要指數代碼
            indices = ["^HSI", "^HSCEI", "0700.HK", "9988.HK", "1398.HK"]

            # 並發獲取指數數據
            tasks = [self.get_stock_price(symbol) for symbol in indices]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            overview = {"timestamp": datetime.now().isoformat(), "indices": {}}

            for symbol, response in zip(indices, responses):
                if not isinstance(response, Exception) and response:
                    overview["indices"][symbol] = response

            return overview

        except Exception as e:
            self.logger.error(f"獲取市場概覽失敗: {e}")
            return None

    async def _get_indicators_from_local(
        self, symbol: str, period: str
    ) -> Optional[Dict[str, Any]]:
        """從本地 API 獲取技術指標"""
        try:
            # 這裡可以調用現有的技術指標計算函數
            # 暫時返回模擬數據
            return {
                "symbol": symbol,
                "period": period,
                "rsi": 50.5,
                "macd": 0.15,
                "ma20": 150.25,
                "ma50": 148.80,
                "volume": 1000000,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"獲取技術指標失敗: {e}")
            return None

    def _convert_to_yahoo_symbol(self, symbol: str) -> str:
        """轉換股票代碼為 Yahoo Finance 格式"""
        if symbol.endswith(".HK"):
            return symbol.replace(".HK", ".HK")
        elif symbol.endswith(".hk"):
            return symbol.replace(".hk", ".HK")
        else:
            return f"{symbol}.HK"

    def _format_price_data(self, data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """格式化價格數據"""
        # 根據實際 API 響應格式進行調整
        return {
            "symbol": symbol,
            "price": data.get("price", 0),
            "change": data.get("change", 0),
            "change_percent": data.get("change_percent", 0),
            "volume": data.get("volume", 0),
            "high": data.get("high", 0),
            "low": data.get("low", 0),
            "open": data.get("open", 0),
            "timestamp": datetime.now().isoformat(),
            "source": "local_api",
        }

    def _format_yahoo_data(self, data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """格式化 Yahoo Finance 數據"""
        try:
            result = data.get("chart", {}).get("result", [])
            if not result:
                return None

            chart_data = result[0]
            timestamps = chart_data.get("timestamp", [])
            indicators = chart_data.get("indicators", {})

            # 獲取最新數據
            if not timestamps or not indicators.get("quote"):
                return None

            latest_index = -1
            quotes = indicators["quote"][latest_index]

            return {
                "symbol": symbol,
                "price": quotes.get("close", 0),
                "change": quotes.get("close", 0) - quotes.get("open", 0),
                "change_percent": 0,  # 需要計算
                "volume": quotes.get("volume", 0),
                "high": quotes.get("high", 0),
                "low": quotes.get("low", 0),
                "open": quotes.get("open", 0),
                "timestamp": datetime.fromtimestamp(
                    timestamps[latest_index]
                ).isoformat(),
                "source": "yahoo_finance",
            }
        except Exception as e:
            self.logger.error(f"格式化 Yahoo 數據失敗: {e}")
            return None

    def _get_cached_data(self, cache_key: str) -> Optional[Any]:
        """獲取緩存數據"""
        if cache_key in self.data_cache:
            cached_item = self.data_cache[cache_key]
            if time.time() - cached_item["timestamp"] < self.cache_ttl:
                return cached_item["data"]
            else:
                del self.data_cache[cache_key]
        return None

    def _cache_data(self, cache_key: str, data: Any):
        """緩存數據"""
        self.data_cache[cache_key] = {"data": data, "timestamp": time.time()}

        # 清理過期緩存
        self._cleanup_expired_cache()

    def _cleanup_expired_cache(self):
        """清理過期緩存"""
        current_time = time.time()
        expired_keys = []

        for key, item in self.data_cache.items():
            if current_time - item["timestamp"] > self.cache_ttl:
                expired_keys.append(key)

        for key in expired_keys:
            del self.data_cache[key]

    def get_statistics(self) -> Dict[str, Any]:
        """獲取服務統計信息"""
        success_rate = 0
        if self.stats["requests_made"] > 0:
            success_rate = (
                self.stats["successful_requests"] / self.stats["requests_made"]
            )

        return {
            "stats": self.stats.copy(),
            "success_rate": success_rate,
            "cache_size": len(self.data_cache),
            "cache_hit_rate": self.stats["cache_hits"]
            / max(self.stats["requests_made"], 1),
        }


# 全局實例
_realtime_service_instance: Optional[RealtimeDataService] = None


def get_realtime_service() -> RealtimeDataService:
    """獲取實時數據服務實例"""
    global _realtime_service_instance
    if _realtime_service_instance is None:
        _realtime_service_instance = RealtimeDataService()
    return _realtime_service_instance


# Telegram Bot 命令處理函數
async def price_cmd(update, context):
    """查詢股價命令 /price <股票代碼>"""
    if not context.args:
        await update.message.reply_text("用法：/price <股票代碼>\n例如：/price 0700.HK")
        return

    symbol = context.args[0].upper()
    await update.message.reply_text(f"正在查詢 {symbol} 的價格，請稍候...")

    try:
        service = get_realtime_service()
        price_data = await service.get_stock_price(symbol)

        if price_data:
            response = f"📈 {price_data['symbol']} 實時價格\n"
            response += f"💰 現價: {price_data['price']:.2f}\n"
            response += f"📊 變動: {price_data['change']:+.2f} ({price_data['change_percent']:+.2f}%)\n"
            response += f"📈 最高: {price_data['high']:.2f}\n"
            response += f"📉 最低: {price_data['low']:.2f}\n"
            response += f"💼 成交量: {price_data['volume']:,}"
            await update.message.reply_text(response)
        else:
            await update.message.reply_text(f"無法獲取 {symbol} 的價格信息")

    except Exception as e:
        logging.error(f"查詢股價失敗: {e}")
        await update.message.reply_text("查詢失敗，請稍後再試。")


async def market_cmd(update, context):
    """市場概覽命令 /market [HK]"""
    market = context.args[0].upper() if context.args else "HK"

    await update.message.reply_text(f"正在獲取 {market} 市場概覽，請稍候...")

    try:
        service = get_realtime_service()
        overview = await service.get_market_overview(market)

        if overview:
            response = f"🏢 {market} 市場概覽\n\n"

            for symbol, data in overview.get("indices", {}).items():
                response += f"📊 {symbol}: {data.get('price', 0):.2f} "
                response += f"({data.get('change_percent', 0):+.2f}%)\n"

            await update.message.reply_text(response)
        else:
            await update.message.reply_text(f"無法獲取 {market} 市場概覽")

    except Exception as e:
        logging.error(f"市場概覽失敗: {e}")
        await update.message.reply_text("查詢失敗，請稍後再試。")

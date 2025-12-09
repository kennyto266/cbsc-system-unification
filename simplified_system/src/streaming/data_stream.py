#!/usr / bin / env python3
"""
Simplified System - Real - time Data Streamer
简化系统 - 实时数据流处理器

高性能实时股票数据流处理核心
High - performance real - time stock data stream processing core
"""

import asyncio
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import aiohttp
import numpy as np
import pandas as pd
import websockets

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from config import get_data_source_config, get_performance_config
from src.api.stock_api import StockDataAPI

logger = logging.getLogger(__name__)


@dataclass
class StockTick:
    """股票Tick数据结构"""

    symbol: str
    timestamp: datetime
    price: float
    volume: int
    bid: Optional[float] = None
    ask: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class TechnicalIndicators:
    """技术指标数据结构"""

    symbol: str
    timestamp: datetime
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_lower: Optional[float] = None
    sma_20: Optional[float] = None
    ema_12: Optional[float] = None
    volume_sma: Optional[float] = None


class RealTimeDataStreamer:
    """
    实时数据流处理器
    支持多股票并行实时数据获取和处理
    """

    def __init__(self, max_concurrent_requests: int = 50):
        # 配置加载
        get_data_source_config()
        perf_config = get_performance_config()

        self.stock_api = StockDataAPI()
        self.max_concurrent_requests = max_concurrent_requests

        # 实时数据缓存
        self._price_cache: Dict[str, StockTick] = {}
        self._indicator_cache: Dict[str, TechnicalIndicators] = {}
        self._subscribers: Dict[str, List[Callable]] = {}

        # 性能配置
        self.update_interval = perf_config.caching.get(
            "api_cache_ttl", 5
        )  # 默认5秒更新
        self.indicator_calculation_interval = 10  # 技术指标10秒计算一次

        # 历史数据用于技术指标计算
        self._historical_data: Dict[str, pd.DataFrame] = {}
        self.max_history_length = 300  # 保留300个历史数据点

        # 异步控制
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._executor = ThreadPoolExecutor(max_workers = 10)

        # 性能统计
        self._stats = {
            "requests_per_second": 0,
            "last_update_time": None,
            "total_updates": 0,
            "error_count": 0,
        }

        logger.info(
            f"RealTime Data Streamer initialized with {max_concurrent_requests} concurrent requests"
        )

    async def start_streaming(self, symbols: List[str]) -> None:
        """
        开始实时数据流

        Args:
            symbols: 股票代码列表
        """
        if self._running:
            logger.warning("Streamer is already running")
            return

        self._running = True
        self._watched_symbols = symbols

        logger.info(f"Starting real - time streaming for {len(symbols)} symbols")

        # 初始化历史数据
        await self._initialize_historical_data(symbols)

        # 启动后台任务
        self._tasks = [
            asyncio.create_task(self._price_update_loop()),
            asyncio.create_task(self._indicator_calculation_loop()),
            asyncio.create_task(self._performance_monitor_loop()),
        ]

        logger.info("Real - time streaming started successfully")

    async def stop_streaming(self) -> None:
        """停止实时数据流"""
        if not self._running:
            return

        self._running = False

        # 取消所有后台任务
        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions = True)

        self._executor.shutdown(wait = True)

        logger.info("Real - time streaming stopped")

    async def _initialize_historical_data(self, symbols: List[str]) -> None:
        """初始化历史数据用于技术指标计算"""
        logger.info("Initializing historical data for technical indicators...")

        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(self._fetch_historical_data(symbol))
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions = True)

        logger.info(
            f"Historical data initialized for {len(self._historical_data)} symbols"
        )

    async def _fetch_historical_data(
        self, symbol: str, duration_days: int = 30
    ) -> None:
        """获取历史数据"""
        try:
            df = self.stock_api.get_stock_prices_dataframe(symbol, duration_days)
            if df is not None and len(df) > 0:
                self._historical_data[symbol] = df.tail(self.max_history_length)
                logger.debug(f"Loaded {len(df)} historical records for {symbol}")
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {symbol}: {e}")

    async def _price_update_loop(self) -> None:
        """价格更新循环"""
        logger.info("Starting price update loop")

        while self._running:
            start_time = time.time()

            try:
                # 并行获取所有股票的实时价格
                tasks = []
                for symbol in self._watched_symbols:
                    task = asyncio.create_task(self._update_single_stock_price(symbol))
                    tasks.append(task)

                # 使用信号量限制并发请求数
                semaphore = asyncio.Semaphore(self.max_concurrent_requests)

                async def bounded_update(task):
                    async with semaphore:
                        return await task

                bounded_tasks = [bounded_update(task) for task in tasks]
                await asyncio.gather(*bounded_tasks, return_exceptions = True)

                # 通知订阅者
                await self._notify_subscribers()

                # 更新性能统计
                self._stats["total_updates"] += 1
                self._stats["last_update_time"] = datetime.now()

            except Exception as e:
                logger.error(f"Error in price update loop: {e}")
                self._stats["error_count"] += 1

            # 控制更新频率
            elapsed = time.time() - start_time
            sleep_time = max(0, self.update_interval - elapsed)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

    async def _update_single_stock_price(self, symbol: str) -> None:
        """更新单个股票的价格数据"""
        try:
            # 获取实时价格
            current_price = self.stock_api.get_real_time_price(symbol)
            if current_price is None:
                return

            current_time = datetime.now()

            # 创建Tick数据
            tick = StockTick(
                symbol = symbol,
                timestamp = current_time,
                price = current_price,
                volume = 0,  # API暂不提供实时成交量
                change = 0.0,  # 需要计算
                change_percent = 0.0,  # 需要计算
            )

            # 计算价格变化
            if symbol in self._price_cache:
                last_price = self._price_cache[symbol].price
                tick.change = current_price - last_price
                tick.change_percent = (
                    (tick.change / last_price) * 100 if last_price > 0 else 0
                )

            # 更新缓存
            self._price_cache[symbol] = tick

            # 更新历史数据
            await self._update_historical_data(symbol, current_price, current_time)

        except Exception as e:
            logger.error(f"Error updating price for {symbol}: {e}")

    async def _update_historical_data(
        self, symbol: str, price: float, timestamp: datetime
    ) -> None:
        """更新历史数据"""
        if symbol not in self._historical_data:
            self._historical_data[symbol] = pd.DataFrame(columns=["price"])

        # 添加新数据点
        new_row = pd.DataFrame({"price": [price]}, index=[timestamp])
        self._historical_data[symbol] = pd.concat(
            [self._historical_data[symbol], new_row]
        )

        # 保持数据长度限制
        if len(self._historical_data[symbol]) > self.max_history_length:
            self._historical_data[symbol] = self._historical_data[symbol].tail(
                self.max_history_length
            )

    async def _indicator_calculation_loop(self) -> None:
        """技术指标计算循环"""
        logger.info("Starting technical indicator calculation loop")

        while self._running:
            try:
                # 并行计算所有股票的技术指标
                tasks = []
                for symbol in self._watched_symbols:
                    if (
                        symbol in self._historical_data
                        and len(self._historical_data[symbol]) >= 14
                    ):
                        task = asyncio.create_task(self._calculate_indicators(symbol))
                        tasks.append(task)

                if tasks:
                    await asyncio.gather(*tasks, return_exceptions = True)

                await asyncio.sleep(self.indicator_calculation_interval)

            except Exception as e:
                logger.error(f"Error in indicator calculation loop: {e}")
                await asyncio.sleep(self.indicator_calculation_interval)

    async def _calculate_indicators(self, symbol: str) -> None:
        """计算技术指标"""
        try:
            df = self._historical_data[symbol]
            if len(df) < 14:
                return

            current_time = datetime.now()

            # 在线程池中计算指标（避免阻塞事件循环）
            indicators = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                self._calculate_indicators_sync,
                df,
                symbol,
                current_time,
            )

            # 更新缓存
            self._indicator_cache[symbol] = indicators

        except Exception as e:
            logger.error(f"Error calculating indicators for {symbol}: {e}")

    def _calculate_indicators_sync(
        self, df: pd.DataFrame, symbol: str, timestamp: datetime
    ) -> TechnicalIndicators:
        """同步计算技术指标（在线程池中执行）"""
        prices = df["price"]

        # RSI (14周期)
        rsi = self._calculate_rsi(prices, 14)

        # MACD (12, 26, 9)
        macd_line, macd_signal = self._calculate_macd(prices, 12, 26, 9)

        # 布林带 (20周期, 2标准差)
        bb_upper, bb_lower = self._calculate_bollinger_bands(prices, 20, 2)

        # SMA (20周期)
        sma_20 = prices.rolling(window = 20).mean().iloc[-1]

        # EMA (12周期)
        ema_12 = prices.ewm(span = 12).mean().iloc[-1]

        return TechnicalIndicators(
            symbol = symbol,
            timestamp = timestamp,
            rsi = rsi,
            macd = macd_line,
            macd_signal = macd_signal,
            bollinger_upper = bb_upper,
            bollinger_lower = bb_lower,
            sma_20 = sma_20,
            ema_12 = ema_12,
        )

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> Optional[float]:
        """计算RSI指标"""
        if len(prices) < period + 1:
            return None

        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window = period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window = period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else None

    def _calculate_macd(
        self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> tuple:
        """计算MACD指标"""
        if len(prices) < slow:
            return None, None

        ema_fast = prices.ewm(span = fast).mean()
        ema_slow = prices.ewm(span = slow).mean()
        macd_line = ema_fast - ema_slow
        macd_signal = macd_line.ewm(span = signal).mean()

        return macd_line.iloc[-1], macd_signal.iloc[-1]

    def _calculate_bollinger_bands(
        self, prices: pd.Series, period: int = 20, std_dev: float = 2
    ) -> tuple:
        """计算布林带"""
        if len(prices) < period:
            return None, None

        sma = prices.rolling(window = period).mean()
        std = prices.rolling(window = period).std()

        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)

        return upper_band.iloc[-1], lower_band.iloc[-1]

    async def _performance_monitor_loop(self) -> None:
        """性能监控循环"""
        logger.info("Starting performance monitor loop")

        while self._running:
            try:
                # 计算每秒请求数
                if self._stats["last_update_time"]:
                    time_diff = (
                        datetime.now() - self._stats["last_update_time"]
                    ).total_seconds()
                    if time_diff > 0:
                        self._stats["requests_per_second"] = (
                            len(self._watched_symbols) / time_diff
                        )

                # 记录性能指标
                if (
                    self._stats["total_updates"] % 100 == 0
                    and self._stats["total_updates"] > 0
                ):
                    logger.info(
                        f"Performance stats - Updates: {self._stats['total_updates']}, "
                        f"RPS: {self._stats['requests_per_second']:.2f}, "
                        f"Errors: {self._stats['error_count']}"
                    )

                await asyncio.sleep(60)  # 每分钟监控一次

            except Exception as e:
                logger.error(f"Error in performance monitor loop: {e}")
                await asyncio.sleep(60)

    async def _notify_subscribers(self) -> None:
        """通知所有订阅者"""
        for symbol, callbacks in self._subscribers.items():
            if symbol in self._price_cache:
                tick_data = self._price_cache[symbol].to_dict()

                for callback in callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(tick_data)
                        else:
                            callback(tick_data)
                    except Exception as e:
                        logger.error(f"Error notifying subscriber for {symbol}: {e}")

    def subscribe(self, symbol: str, callback: Callable) -> None:
        """
        订阅股票数据更新

        Args:
            symbol: 股票代码
            callback: 回调函数
        """
        if symbol not in self._subscribers:
            self._subscribers[symbol] = []

        self._subscribers[symbol].append(callback)
        logger.info(f"New subscriber for {symbol}")

    def unsubscribe(self, symbol: str, callback: Callable) -> None:
        """
        取消订阅

        Args:
            symbol: 股票代码
            callback: 回调函数
        """
        if symbol in self._subscribers:
            try:
                self._subscribers[symbol].remove(callback)
                logger.info(f"Unsubscribed from {symbol}")
            except ValueError:
                pass

    def get_latest_tick(self, symbol: str) -> Optional[StockTick]:
        """获取最新Tick数据"""
        return self._price_cache.get(symbol)

    def get_latest_indicators(self, symbol: str) -> Optional[TechnicalIndicators]:
        """获取最新技术指标"""
        return self._indicator_cache.get(symbol)

    def get_all_latest_data(self) -> Dict[str, Dict[str, Any]]:
        """获取所有股票的最新数据"""
        result = {}

        for symbol in self._watched_symbols:
            symbol_data = {}

            # 价格数据
            if symbol in self._price_cache:
                symbol_data["tick"] = self._price_cache[symbol].to_dict()

            # 技术指标
            if symbol in self._indicator_cache:
                symbol_data["indicators"] = asdict(self._indicator_cache[symbol])
                symbol_data["indicators"]["timestamp"] = self._indicator_cache[
                    symbol
                ].timestamp.isoformat()

            if symbol_data:
                result[symbol] = symbol_data

        return result

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return {
            **self._stats,
            "watched_symbols_count": (
                len(self._watched_symbols) if hasattr(self, "_watched_symbols") else 0
            ),
            "subscriber_count": sum(
                len(callbacks) for callbacks in self._subscribers.values()
            ),
            "cache_sizes": {
                "price_cache": len(self._price_cache),
                "indicator_cache": len(self._indicator_cache),
                "historical_data": len(self._historical_data),
            },
        }

    async def add_symbol(self, symbol: str) -> None:
        """动态添加监控股票"""
        if hasattr(self, "_watched_symbols") and symbol not in self._watched_symbols:
            self._watched_symbols.append(symbol)
            await self._fetch_historical_data(symbol)
            logger.info(f"Added new symbol to watch: {symbol}")

    async def remove_symbol(self, symbol: str) -> None:
        """动态移除监控股票"""
        if hasattr(self, "_watched_symbols") and symbol in self._watched_symbols:
            self._watched_symbols.remove(symbol)

            # 清理缓存
            self._price_cache.pop(symbol, None)
            self._indicator_cache.pop(symbol, None)
            self._historical_data.pop(symbol, None)
            self._subscribers.pop(symbol, None)

            logger.info(f"Removed symbol from watch: {symbol}")


# 全局实例
_streamer = None


def get_streamer() -> RealTimeDataStreamer:
    """获取全局数据流处理器实例"""
    global _streamer
    if _streamer is None:
        _streamer = RealTimeDataStreamer()
    return _streamer


if __name__ == "__main__":

    async def test_streamer():
        """测试实时数据流处理器"""
        streamer = RealTimeDataStreamer()

        # 测试回调函数
        async def price_callback(data):
            print(f"Price update: {data['symbol']} - ${data['price']:.2f}")

        # 订阅腾讯
        streamer.subscribe("0700.hk", price_callback)

        # 开始流式传输
        symbols = ["0700.hk", "0941.hk", "1398.hk"]
        await streamer.start_streaming(symbols)

        # 运行30秒
        await asyncio.sleep(30)

        # 停止
        await streamer.stop_streaming()

        # 打印统计信息
        stats = streamer.get_performance_stats()
        print(f"Performance stats: {stats}")

    # 运行测试
    asyncio.run(test_streamer())

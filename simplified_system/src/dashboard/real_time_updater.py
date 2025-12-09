#!/usr / bin / env python3
"""
实时数据更新器
Real Time Data Updater

处理仪表板的实时数据更新，包括：
- WebSocket连接管理
- 数据流处理
- 定时数据获取
- 连接状态监控
- 错误处理和重连
"""

import logging
import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Optional

import numpy as np
import pandas as pd
import requests

from ..api.government_data import get_hibor_data, get_latest_hibor

# 导入系统组件
from ..api.stock_api import get_hk_stock_data

logger = logging.getLogger(__name__)


@dataclass
class RealTimeData:
    """实时数据结构"""

    symbol: str
    timestamp: datetime
    price: float
    volume: float
    change: float
    change_percent: float
    indicators: Dict[str, float] = None


@dataclass
class WebSocketMessage:
    """WebSocket消息结构"""

    type: str  # 'price', 'indicator', 'status'
    data: Dict[str, Any]
    timestamp: datetime


class RealTimeUpdater:
    """实时数据更新器"""

    def __init__(self, update_interval: int = 30):
        """
        初始化实时更新器

        Args:
            update_interval: 更新间隔（秒）
        """
        self.update_interval = update_interval
        self.is_running = False
        self.update_thread = None
        self.websocket_thread = None

        # 数据缓存
        self.data_cache = {}
        self.update_queue = queue.Queue()

        # 回调函数
        self.update_callbacks = []

        # WebSocket连接
        self.websocket_connections = []
        self.websocket_url = None

        # 数据源配置
        self.data_sources = {
            "stock_api": {
                "enabled": True,
                "symbols": ["0700.HK", "09988.HK", "03690.HK"],
                "update_interval": 30,
            },
            "government_data": {
                "enabled": True,
                "indicators": ["hibor", "exchange_rate", "monetary_base"],
                "update_interval": 300,  # 5分钟
            },
        }

        # 统计信息
        self.stats = {
            "total_updates": 0,
            "successful_updates": 0,
            "failed_updates": 0,
            "last_update": None,
            "average_update_time": 0.0,
        }

        logger.info("Real Time Updater initialized")

    def add_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        添加更新回调函数

        Args:
            callback: 回调函数，接收更新数据作为参数
        """
        self.update_callbacks.append(callback)
        logger.info(f"Added update callback: {callback.__name__}")

    def remove_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        移除更新回调函数

        Args:
            callback: 要移除的回调函数
        """
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
            logger.info(f"Removed update callback: {callback.__name__}")

    def start(self):
        """启动实时更新"""
        if self.is_running:
            logger.warning("Real time updater is already running")
            return

        self.is_running = True

        # 启动更新线程
        self.update_thread = threading.Thread(
            target = self._update_loop, name="RealTimeUpdater", daemon = True
        )
        self.update_thread.start()

        # 启动WebSocket连接
        self.websocket_thread = threading.Thread(
            target = self._websocket_loop, name="WebSocketManager", daemon = True
        )
        self.websocket_thread.start()

        logger.info("Real time updater started")

    def stop(self):
        """停止实时更新"""
        self.is_running = False

        # 等待线程结束
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout = 5)

        if self.websocket_thread and self.websocket_thread.is_alive():
            self.websocket_thread.join(timeout = 5)

        # 关闭WebSocket连接
        for ws in self.websocket_connections:
            try:
                ws.close()
            except Exception:
                pass

        self.websocket_connections.clear()

        logger.info("Real time updater stopped")

    def _update_loop(self):
        """主更新循环"""
        logger.info("Update loop started")

        while self.is_running:
            try:
                start_time = time.time()

                # 更新所有数据源
                update_data = self._update_all_sources()

                if update_data:
                    # 通知回调函数
                    self._notify_callbacks(update_data)

                    # 更新统计信息
                    self._update_stats(time.time() - start_time, True)

                    # 将数据放入队列
                    self.update_queue.put(
                        {
                            "type": "update",
                            "data": update_data,
                            "timestamp": datetime.now(),
                        }
                    )

                else:
                    self._update_stats(time.time() - start_time, False)

                # 等待下一次更新
                time.sleep(self.update_interval)

            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                time.sleep(5)  # 错误时短暂等待

    def _websocket_loop(self):
        """WebSocket连接循环"""
        logger.info("WebSocket loop started")

        while self.is_running:
            try:
                # 这里可以实现WebSocket连接
                # 目前使用模拟数据
                self._simulate_websocket_data()

                time.sleep(1)  # 快速检查WebSocket状态

            except Exception as e:
                logger.error(f"Error in WebSocket loop: {e}")
                time.sleep(5)

    def _update_all_sources(self) -> Optional[Dict[str, Any]]:
        """更新所有数据源"""
        update_data = {}

        try:
            # 更新股票数据
            if self.data_sources["stock_api"]["enabled"]:
                stock_data = self._update_stock_data()
                update_data["stocks"] = stock_data

            # 更新政府数据
            if self.data_sources["government_data"]["enabled"]:
                gov_data = self._update_government_data()
                update_data["government"] = gov_data

            # 添加时间戳
            update_data["timestamp"] = datetime.now().isoformat()

            return update_data

        except Exception as e:
            logger.error(f"Error updating all sources: {e}")
            return None

    def _update_stock_data(self) -> Dict[str, Any]:
        """更新股票数据"""
        stock_data = {}

        try:
            for symbol in self.data_sources["stock_api"]["symbols"]:
                # 获取最新数据（较短时间范围）
                data = get_hk_stock_data(symbol, duration_days = 30)

                if not data.empty:
                    latest = data.iloc[-1]
                    previous = data.iloc[-2] if len(data) > 1 else latest

                    # 计算变化
                    change = latest["close"] - previous["close"]
                    change_percent = (
                        (change / previous["close"]) * 100
                        if previous["close"] != 0
                        else 0
                    )

                    # 计算技术指标
                    indicators = self._calculate_indicators(data)

                    stock_data[symbol] = {
                        "price": float(latest["close"]),
                        "volume": float(latest["volume"]),
                        "change": float(change),
                        "change_percent": float(change_percent),
                        "high": float(latest["high"]),
                        "low": float(latest["low"]),
                        "open": float(latest["open"]),
                        "indicators": indicators,
                        "timestamp": (
                            latest.name.isoformat()
                            if hasattr(latest.name, "isoformat")
                            else str(latest.name)
                        ),
                    }

                    # 缓存数据
                    self.data_cache[symbol] = stock_data[symbol]

            return stock_data

        except Exception as e:
            logger.error(f"Error updating stock data: {e}")
            return {}

    def _update_government_data(self) -> Dict[str, Any]:
        """更新政府数据"""
        gov_data = {}

        try:
            # 获取HIBOR数据
            try:
                hibor_data = get_hibor_data(7)  # 最近7天
                if hibor_data:
                    latest_hibor = (
                        hibor_data[0] if isinstance(hibor_data, list) else hibor_data
                    )
                    gov_data["hibor"] = {
                        "overnight": latest_hibor.get("overnight", 0),
                        "1_week": latest_hibor.get("1_week", 0),
                        "1_month": latest_hibor.get("1_month", 0),
                        "3_month": latest_hibor.get("3_month", 0),
                        "timestamp": latest_hibor.get(
                            "date", datetime.now().isoformat()
                        ),
                    }
            except Exception as e:
                logger.warning(f"Error getting HIBOR data: {e}")

            # 这里可以添加更多政府数据源
            # 例如：汇率、货币基础等

            return gov_data

        except Exception as e:
            logger.error(f"Error updating government data: {e}")
            return {}

    def _calculate_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """计算技术指标"""
        indicators = {}

        try:
            from ..indicators.core_indicators import CoreIndicators

            indicators_engine = CoreIndicators()

            # RSI
            if len(data) >= 14:
                rsi = indicators_engine.calculate_rsi(data["close"], 14)
                indicators["rsi_14"] = float(rsi.iloc[-1]) if not rsi.empty else 0.0

            # 移动平均
            if len(data) >= 20:
                sma_20 = indicators_engine.calculate_sma(data["close"], 20)
                indicators["sma_20"] = (
                    float(sma_20.iloc[-1]) if not sma_20.empty else 0.0
                )

            if len(data) >= 50:
                sma_50 = indicators_engine.calculate_sma(data["close"], 50)
                indicators["sma_50"] = (
                    float(sma_50.iloc[-1]) if not sma_50.empty else 0.0
                )

            # MACD
            if len(data) >= 26:
                macd_result = indicators_engine.calculate_macd(data["close"], 12, 26, 9)
                indicators["macd"] = (
                    float(macd_result["macd"].iloc[-1])
                    if not macd_result["macd"].empty
                    else 0.0
                )
                indicators["macd_signal"] = (
                    float(macd_result["signal"].iloc[-1])
                    if not macd_result["signal"].empty
                    else 0.0
                )

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")

        return indicators

    def _notify_callbacks(self, data: Dict[str, Any]):
        """通知所有回调函数"""
        for callback in self.update_callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in callback {callback.__name__}: {e}")

    def _update_stats(self, update_time: float, success: bool):
        """更新统计信息"""
        self.stats["total_updates"] += 1

        if success:
            self.stats["successful_updates"] += 1
        else:
            self.stats["failed_updates"] += 1

        self.stats["last_update"] = datetime.now()

        # 更新平均更新时间
        total_time = (
            self.stats["average_update_time"] * (self.stats["total_updates"] - 1)
            + update_time
        )
        self.stats["average_update_time"] = total_time / self.stats["total_updates"]

    def _simulate_websocket_data(self):
        """模拟WebSocket数据推送"""
        if not self.is_running:
            return

        # 模拟价格变化
        for symbol in self.data_sources["stock_api"]["symbols"]:
            if symbol in self.data_cache:
                cached_data = self.data_cache[symbol]

                # 模拟小幅价格波动
                price_change = np.random.normal(
                    0, cached_data["price"] * 0.001
                )  # 0.1%标准差
                new_price = max(cached_data["price"] + price_change, 0.01)

                # 更新缓存
                cached_data["price"] = new_price
                cached_data["change"] += price_change
                cached_data["change_percent"] = (
                    cached_data["change"] / cached_data["price"]
                ) * 100
                cached_data["timestamp"] = datetime.now().isoformat()

                # 推送更新
                ws_message = WebSocketMessage(
                    type="price_update",
                    data={symbol: cached_data},
                    timestamp = datetime.now(),
                )

                self.update_queue.put(
                    {
                        "type": "websocket",
                        "data": ws_message.data,
                        "timestamp": ws_message.timestamp,
                    }
                )

    def get_latest_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取最新数据

        Args:
            symbol: 股票代码

        Returns:
            最新数据字典或None
        """
        return self.data_cache.get(symbol)

    def get_all_latest_data(self) -> Dict[str, Any]:
        """获取所有最新数据"""
        return self.data_cache.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "is_running": self.is_running,
            "active_callbacks": len(self.update_callbacks),
            "cached_symbols": list(self.data_cache.keys()),
            "queue_size": self.update_queue.qsize(),
        }

    def add_symbol(self, symbol: str):
        """
        添加要监控的股票

        Args:
            symbol: 股票代码
        """
        if symbol not in self.data_sources["stock_api"]["symbols"]:
            self.data_sources["stock_api"]["symbols"].append(symbol)
            logger.info(f"Added symbol to monitoring: {symbol}")

    def remove_symbol(self, symbol: str):
        """
        移除监控的股票

        Args:
            symbol: 股票代码
        """
        if symbol in self.data_sources["stock_api"]["symbols"]:
            self.data_sources["stock_api"]["symbols"].remove(symbol)
            if symbol in self.data_cache:
                del self.data_cache[symbol]
            logger.info(f"Removed symbol from monitoring: {symbol}")

    def set_update_interval(self, interval: int):
        """
        设置更新间隔

        Args:
            interval: 更新间隔（秒）
        """
        self.update_interval = max(1, interval)
        self.data_sources["stock_api"]["update_interval"] = self.update_interval
        logger.info(f"Update interval set to {self.update_interval} seconds")


# 便利函数
def create_real_time_updater(update_interval: int = 30) -> RealTimeUpdater:
    """创建实时更新器实例"""
    return RealTimeUpdater(update_interval = update_interval)


# 全局实时更新器实例
_global_updater = None


def get_global_updater() -> RealTimeUpdater:
    """获取全局实时更新器实例"""
    global _global_updater
    if _global_updater is None:
        _global_updater = RealTimeUpdater()
    return _global_updater

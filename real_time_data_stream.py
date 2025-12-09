#!/usr/bin/env python3
"""
Simplified System - Real-Time Data Stream Engine
高性能實時數據流處理系統

功能特性:
1. 實時股票數據流處理
2. 低延遲數據更新 (<100ms)
3. 流式技術指標計算
4. 實時信號生成
5. 數據品質監控
6. 自動故障恢復

Author: Claude Code Assistant
Date: 2025-11-27
Version: 1.0.0
"""

import asyncio
import websockets
import json
import time
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, AsyncGenerator
from datetime import datetime, timedelta
import logging

import numpy as np
import pandas as pd
import requests
from collections import deque
import weakref

# 性能監控
import psutil
from prometheus_client import Counter, Gauge, Histogram, start_http_server

# 異步處理
import aiohttp
import asyncpg

# 數據處理
import msgpack
import lz4.frame

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StreamConfig:
    """數據流配置"""
    # 數據源配置
    data_source_url: str = "ws://localhost:8765/realtime"
    backup_data_url: str = "http://18.180.162.113:9191/realtime"
    symbols: List[str] = field(default_factory=lambda: ["0700.HK", "0941.HK", "1398.HK"])

    # 性能配置
    max_latency_ms: int = 100  # 最大延遲
    buffer_size: int = 1000    # 緩衝區大小
    batch_size: int = 50       # 批處理大小
    update_interval_ms: int = 1000  # 更新間隔

    # 可靠性配置
    max_retries: int = 3
    retry_delay_ms: int = 5000
    heartbeat_interval_s: int = 30

    # 數據品質配置
    price_change_threshold: float = 0.20  # 20%價格變化閾值
    volume_spike_threshold: float = 10.0   # 10倍成交量突增閾值
    data_timeout_s: int = 300             # 5分鐘數據超時

@dataclass
class StreamMetrics:
    """數據流指標"""
    messages_received: int = 0
    messages_processed: int = 0
    errors_count: int = 0
    reconnections_count: int = 0

    # 延遲指標
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')

    # 數據品質指標
    data_quality_score: float = 1.0
    missing_data_count: int = 0
    anomaly_count: int = 0

    # 系統指標
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    buffer_utilization: float = 0.0

class DataQualityMonitor:
    """數據品質監控器"""

    def __init__(self, config: StreamConfig):
        self.config = config
        self.price_history = {}
        self.volume_history = {}
        self.last_update_time = {}

    def check_data_quality(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """檢查數據品質"""
        quality_issues = []

        try:
            timestamp = datetime.now()
            price = float(data.get('price', 0))
            volume = int(data.get('volume', 0))

            # 初始化歷史數據
            if symbol not in self.price_history:
                self.price_history[symbol] = deque(maxlen=100)
                self.volume_history[symbol] = deque(maxlen=100)
                self.last_update_time[symbol] = timestamp

            # 檢查價格合理性
            if self.price_history[symbol]:
                last_price = self.price_history[symbol][-1]
                price_change = abs(price - last_price) / last_price if last_price > 0 else 0

                if price_change > self.config.price_change_threshold:
                    quality_issues.append({
                        'type': 'price_anomaly',
                        'severity': 'high',
                        'message': f'Price change {price_change:.2%} exceeds threshold',
                        'data': {'current_price': price, 'last_price': last_price}
                    })

            # 檢查成交量突增
            if self.volume_history[symbol]:
                avg_volume = np.mean(list(self.volume_history[symbol])[-20:])  # 20期均值
                if avg_volume > 0 and volume > avg_volume * self.config.volume_spike_threshold:
                    quality_issues.append({
                        'type': 'volume_spike',
                        'severity': 'medium',
                        'message': f'Volume spike detected: {volume:,} vs avg {avg_volume:,.0f}',
                        'data': {'current_volume': volume, 'avg_volume': avg_volume}
                    })

            # 檢查數據更新時間
            time_since_last = (timestamp - self.last_update_time[symbol]).total_seconds()
            if time_since_last > self.config.data_timeout_s:
                quality_issues.append({
                    'type': 'data_timeout',
                    'severity': 'high',
                    'message': f'Data timeout: {time_since_last:.1f}s since last update',
                    'data': {'timeout_seconds': time_since_last}
                })

            # 更新歷史數據
            self.price_history[symbol].append(price)
            self.volume_history[symbol].append(volume)
            self.last_update_time[symbol] = timestamp

            # 計算品質分數 (0-1)
            quality_score = max(0, 1.0 - len([i for i in quality_issues if i['severity'] == 'high']) * 0.3)

            return {
                'quality_score': quality_score,
                'issues': quality_issues,
                'timestamp': timestamp.isoformat(),
                'symbol': symbol
            }

        except Exception as e:
            logger.error(f"Error in data quality check for {symbol}: {e}")
            return {
                'quality_score': 0.0,
                'issues': [{'type': 'check_error', 'severity': 'high', 'message': str(e)}],
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol
            }

class RealTimeDataProcessor:
    """實時數據處理器"""

    def __init__(self, config: StreamConfig):
        self.config = config
        self.indicators_cache = {}
        self.last_processed_data = {}

    def calculate_streaming_indicators(self, symbol: str, new_data: Dict[str, Any]) -> Dict[str, float]:
        """計算流式技術指標"""
        try:
            price = float(new_data.get('price', 0))
            volume = int(new_data.get('volume', 0))
            timestamp = datetime.now()

            # 初始化緩存
            if symbol not in self.indicators_cache:
                self.indicators_cache[symbol] = {
                    'prices': deque(maxlen=100),
                    'volumes': deque(maxlen=100),
                    'timestamps': deque(maxlen=100),
                    'rsi_values': deque(maxlen=100),
                    'ma_short': deque(maxlen=50),
                    'ma_long': deque(maxlen=200)
                }

            cache = self.indicators_cache[symbol]

            # 更新數據
            cache['prices'].append(price)
            cache['volumes'].append(volume)
            cache['timestamps'].append(timestamp)

            indicators = {}

            if len(cache['prices']) >= 14:
                # RSI (14期)
                prices_array = np.array(list(cache['prices']))
                deltas = np.diff(prices_array)
                gains = np.where(deltas > 0, deltas, 0)
                losses = np.where(deltas < 0, -deltas, 0)

                if len(gains) >= 14:
                    avg_gain = np.mean(gains[-14:])
                    avg_loss = np.mean(losses[-14:])

                    if avg_loss > 0:
                        rs = avg_gain / avg_loss
                        rsi = 100 - (100 / (1 + rs))
                        indicators['rsi_14'] = rsi / 100.0  # 正規化到0-1

            if len(cache['prices']) >= 20:
                # 移動平均
                prices_array = np.array(list(cache['prices']))

                # 20期移動平均
                ma_20 = np.mean(prices_array[-20:])
                indicators['ma_20'] = ma_20
                indicators['price_ma_20_ratio'] = price / ma_20 - 1

                # 布林帶
                std_20 = np.std(prices_array[-20:])
                bb_upper = ma_20 + 2 * std_20
                bb_lower = ma_20 - 2 * std_20
                indicators['bb_position'] = (price - bb_lower) / (bb_upper - bb_lower)

            if len(cache['prices']) >= 10:
                # 動量指標
                prices_array = np.array(list(cache['prices']))
                indicators['momentum_10'] = (price - prices_array[-10]) / prices_array[-10]

            if len(cache['volumes']) >= 20:
                # 成交量指標
                volumes_array = np.array(list(cache['volumes']))
                avg_volume = np.mean(volumes_array[-20:])
                indicators['volume_ratio'] = volume / avg_volume

                # 價量趨勢
                price_changes = np.diff(prices_array[-20:]) if len(prices_array) >= 20 else [0]
                volume_changes = np.diff(volumes_array[-20:]) if len(volumes_array) >= 20 else [0]

                if len(price_changes) > 0 and len(volume_changes) > 0:
                    pvt = np.sum(price_changes * volume_changes[-len(price_changes):])
                    indicators['pvt'] = pvt / 1e6  # 正規化

            # 波動率
            if len(cache['prices']) >= 20:
                prices_array = np.array(list(cache['prices']))
                returns = np.diff(prices_array) / prices_array[:-1]
                volatility = np.std(returns[-20:]) * np.sqrt(252)
                indicators['volatility'] = volatility

            self.last_processed_data[symbol] = {
                'timestamp': timestamp,
                'price': price,
                'indicators': indicators
            }

            return indicators

        except Exception as e:
            logger.error(f"Error calculating streaming indicators for {symbol}: {e}")
            return {}

class RealTimeDataStream:
    """
    實時數據流引擎

    提供低延遲、高可靠性的實時數據處理功能
    """

    def __init__(self, config: Optional[StreamConfig] = None):
        self.config = config or StreamConfig()
        self.metrics = StreamMetrics()
        self.data_queue = asyncio.Queue(maxsize=self.config.buffer_size)
        self.processed_data = asyncio.Queue(maxsize=self.config.buffer_size)

        # 組件初始化
        self.quality_monitor = DataQualityMonitor(self.config)
        self.data_processor = RealTimeDataProcessor(self.config)

        # 狀態管理
        self.is_running = False
        self.websocket = None
        self.session = None
        self.subscribers = {}

        # 性能監控
        self.latency_buffer = deque(maxlen=1000)
        self.start_time = time.time()

        # 設置Prometheus指標
        self._setup_metrics()

        logger.info("RealTimeDataStream initialized")

    def _setup_metrics(self):
        """設置性能監控指標"""
        self.prometheus_metrics = {
            'messages_total': Counter('stream_messages_total', 'Total messages received'),
            'latency_seconds': Histogram('stream_latency_seconds', 'Message latency'),
            'errors_total': Counter('stream_errors_total', 'Total errors'),
            'active_subscriptions': Gauge('stream_active_subscriptions', 'Active subscriptions'),
            'buffer_size': Gauge('stream_buffer_size', 'Buffer size')
        }

    async def connect_websocket(self):
        """連接WebSocket數據源"""
        retry_count = 0

        while retry_count < self.config.max_retries:
            try:
                logger.info(f"Connecting to WebSocket: {self.config.data_source_url}")

                self.websocket = await websockets.connect(
                    self.config.data_source_url,
                    ping_interval=self.config.heartbeat_interval_s,
                    ping_timeout=self.config.heartbeat_interval_s * 2,
                    close_timeout=self.config.heartbeat_interval_s
                )

                # 訂閱股票數據
                subscribe_msg = {
                    'action': 'subscribe',
                    'symbols': self.config.symbols,
                    'data_type': 'quote'
                }

                await self.websocket.send(json.dumps(subscribe_msg))
                logger.info(f"Subscribed to {len(self.config.symbols)} symbols")

                return True

            except Exception as e:
                retry_count += 1
                logger.error(f"WebSocket connection failed (attempt {retry_count}): {e}")

                if retry_count < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay_ms / 1000)

        return False

    async def fallback_to_http(self):
        """回退到HTTP數據源"""
        logger.info("Falling back to HTTP data source")

        async with aiohttp.ClientSession() as session:
            while self.is_running:
                try:
                    for symbol in self.config.symbols:
                        start_time = time.time()

                        # 模擬HTTP實時數據請求
                        url = f"{self.config.backup_data_url}/quote/{symbol}"

                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                            if response.status == 200:
                                data = await response.json()

                                # 添加時間戳
                                data['timestamp'] = datetime.now().isoformat()
                                data['symbol'] = symbol

                                # 計算延遲
                                latency = (time.time() - start_time) * 1000
                                self._update_latency_metrics(latency)

                                # 加入處理隊列
                                await self.data_queue.put({
                                    'source': 'http_fallback',
                                    'data': data,
                                    'timestamp': time.time()
                                })

                                self.prometheus_metrics['messages_total'].inc()

                    await asyncio.sleep(self.config.update_interval_ms / 1000)

                except Exception as e:
                    logger.error(f"HTTP fallback error: {e}")
                    await asyncio.sleep(5)

    async def websocket_listener(self):
        """WebSocket監聽器"""
        try:
            async for message in self.websocket:
                if not self.is_running:
                    break

                start_time = time.time()

                try:
                    # 解析消息
                    data = json.loads(message)

                    # 計算延遲
                    if 'timestamp' in data:
                        message_time = datetime.fromisoformat(data['timestamp'])
                        latency = (datetime.now() - message_time).total_seconds() * 1000
                        self._update_latency_metrics(latency)

                    # 加入處理隊列
                    await self.data_queue.put({
                        'source': 'websocket',
                        'data': data,
                        'timestamp': time.time()
                    })

                    self.prometheus_metrics['messages_total'].inc()
                    self.metrics.messages_received += 1

                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    self.metrics.errors_count += 1
                    self.prometheus_metrics['errors_total'].inc()

        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.metrics.reconnections_count += 1
        except Exception as e:
            logger.error(f"WebSocket listener error: {e}")
            self.metrics.errors_count += 1
            self.prometheus_metrics['errors_total'].inc()

    async def data_processor_task(self):
        """數據處理任務"""
        batch = []

        while self.is_running:
            try:
                # 等待數據或超時
                try:
                    item = await asyncio.wait_for(self.data_queue.get(), timeout=1.0)
                    batch.append(item)
                except asyncio.TimeoutError:
                    pass

                # 批處理或達到批大小
                if len(batch) >= self.config.batch_size or (batch and time.time() - batch[0]['timestamp'] > 0.1):
                    processed_batch = await self._process_batch(batch)

                    # 發送給訂閱者
                    for processed_item in processed_batch:
                        await self.processed_data.put(processed_item)

                        # 通知訂閱者
                        await self._notify_subscribers(processed_item)

                    batch = []
                    self.metrics.messages_processed += len(processed_batch)

                # 更新系統指標
                self._update_system_metrics()

            except Exception as e:
                logger.error(f"Data processor error: {e}")
                self.metrics.errors_count += 1

    async def _process_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """處理數據批次"""
        processed_items = []

        for item in batch:
            try:
                data = item['data']
                symbol = data.get('symbol', 'UNKNOWN')

                # 數據品質檢查
                quality_report = self.quality_monitor.check_data_quality(symbol, data)

                # 計算流式指標
                indicators = self.data_processor.calculate_streaming_indicators(symbol, data)

                # 組合處理後的數據
                processed_item = {
                    'symbol': symbol,
                    'raw_data': data,
                    'indicators': indicators,
                    'quality': quality_report,
                    'source': item['source'],
                    'processing_timestamp': datetime.now().isoformat(),
                    'latency_ms': (time.time() - item['timestamp']) * 1000
                }

                processed_items.append(processed_item)

                # 更新品質指標
                self.metrics.data_quality_score = quality_report['quality_score']

                if quality_report['issues']:
                    self.metrics.anomaly_count += len(quality_report['issues'])

            except Exception as e:
                logger.error(f"Error processing batch item: {e}")
                self.metrics.errors_count += 1

        return processed_items

    async def _notify_subscribers(self, data: Dict[str, Any]):
        """通知所有訂閱者"""
        symbol = data['symbol']

        if symbol in self.subscribers:
            for callback in self.subscribers[symbol].copy():
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        # 在線程池中執行同步回調
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, callback, data)
                except Exception as e:
                    logger.error(f"Error notifying subscriber: {e}")

    def subscribe(self, symbol: str, callback: Callable):
        """訂閱股票數據"""
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []

        self.subscribers[symbol].append(callback)
        self.prometheus_metrics['active_subscriptions'].inc()

        logger.info(f"Subscribed to {symbol} updates")

    def unsubscribe(self, symbol: str, callback: Callable):
        """取消訂閱"""
        if symbol in self.subscribers and callback in self.subscribers[symbol]:
            self.subscribers[symbol].remove(callback)
            self.prometheus_metrics['active_subscriptions'].dec()

            if not self.subscribers[symbol]:
                del self.subscribers[symbol]

            logger.info(f"Unsubscribed from {symbol}")

    async def get_real_time_data(self, symbol: str, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """獲取實時數據"""
        end_time = time.time() + timeout

        while time.time() < end_time:
            try:
                # 檢查處理後的數據隊列
                item = await asyncio.wait_for(self.processed_data.get(), timeout=0.1)

                if item['symbol'] == symbol:
                    return item

                # 放回隊列給其他訂閱者
                await self.processed_data.put(item)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error getting real-time data: {e}")

        return None

    def _update_latency_metrics(self, latency_ms: float):
        """更新延遲指標"""
        self.latency_buffer.append(latency_ms)

        self.metrics.avg_latency_ms = np.mean(self.latency_buffer)
        self.metrics.max_latency_ms = max(self.latency_buffer)
        self.metrics.min_latency_ms = min(self.latency_buffer)

        self.prometheus_metrics['latency_seconds'].observe(latency_ms / 1000)

    def _update_system_metrics(self):
        """更新系統指標"""
        self.metrics.memory_usage_mb = psutil.Process().memory_info().rss / 1024 / 1024
        self.metrics.cpu_usage_percent = psutil.cpu_percent()
        self.metrics.buffer_utilization = self.data_queue.qsize() / self.config.buffer_size

        self.prometheus_metrics['buffer_size'].set(self.data_queue.qsize())

    def get_metrics(self) -> Dict[str, Any]:
        """獲取性能指標"""
        uptime = time.time() - self.start_time

        return {
            'uptime_seconds': uptime,
            'messages_per_second': self.metrics.messages_received / uptime if uptime > 0 else 0,
            'processing_rate': self.metrics.messages_processed / uptime if uptime > 0 else 0,
            'error_rate': self.metrics.errors_count / max(1, self.metrics.messages_received),
            'metrics': self.metrics.__dict__,
            'active_subscriptions': sum(len(callbacks) for callbacks in self.subscribers.values()),
            'queue_sizes': {
                'input': self.data_queue.qsize(),
                'processed': self.processed_data.qsize()
            }
        }

    async def start(self):
        """啟動數據流"""
        if self.is_running:
            logger.warning("Data stream is already running")
            return

        self.is_running = True
        logger.info("Starting real-time data stream")

        # 啟動HTTP監控服務
        try:
            start_http_server(8000)
            logger.info("Prometheus metrics server started on port 8000")
        except Exception as e:
            logger.warning(f"Failed to start metrics server: {e}")

        # 連接WebSocket
        if await self.connect_websocket():
            # 啟動WebSocket監聽器
            listener_task = asyncio.create_task(self.websocket_listener())

            # 啟動數據處理器
            processor_task = asyncio.create_task(self.data_processor_task())

            logger.info("Real-time data stream started successfully")

            # 等待任務完成
            await asyncio.gather(listener_task, processor_task, return_exceptions=True)

        else:
            logger.warning("WebSocket connection failed, using HTTP fallback")
            await self.fallback_to_http()

    async def stop(self):
        """停止數據流"""
        self.is_running = False

        if self.websocket:
            await self.websocket.close()

        # 清空隊列
        while not self.data_queue.empty():
            try:
                self.data_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        logger.info("Real-time data stream stopped")

# 使用示例和測試
async def test_realtime_stream():
    """測試實時數據流"""
    config = StreamConfig(
        symbols=["0700.HK", "0941.HK"],
        update_interval_ms=2000,
        buffer_size=100
    )

    stream = RealTimeDataStream(config)

    # 定義數據處理回調
    async def data_handler(data):
        symbol = data['symbol']
        price = data['raw_data'].get('price', 0)
        indicators = data['indicators']
        quality = data['quality']

        print(f"[{symbol}] Price: {price}, Quality: {quality['quality_score']:.2f}")

        if indicators:
            print(f"  RSI: {indicators.get('rsi_14', 'N/A'):.3f}")
            print(f"  MA Ratio: {indicators.get('price_ma_20_ratio', 'N/A'):.3f}")

    # 訂閱數據
    stream.subscribe("0700.HK", data_handler)

    try:
        # 啟動數據流
        await asyncio.wait_for(stream.start(), timeout=30)

    except asyncio.TimeoutError:
        print("Test completed")
    finally:
        await stream.stop()

        # 打印性能指標
        metrics = stream.get_metrics()
        print("\nPerformance Metrics:")
        print(json.dumps(metrics, indent=2, default=str))

if __name__ == "__main__":
    # 運行測試
    asyncio.run(test_realtime_stream())
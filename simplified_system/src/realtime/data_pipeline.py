#!/usr/bin/env python3
"""
高性能數據處理管道 - High-Performance Data Processing Pipeline
實時市場數據處理，目標延遲<1ms
Real-time market data processing with <1ms latency target
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import numpy as np
import pandas as pd
from collections import deque
import aioredis
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp
import threading
import queue
import psutil
import gc

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MarketDataPoint:
    """市場數據點"""
    symbol: str
    timestamp: datetime
    price: float
    volume: int
    bid: float
    ask: float
    source: str
    processing_time: float = 0.0

@dataclass
class ProcessedSignal:
    """處理後的信號"""
    symbol: str
    timestamp: datetime
    signal_type: str  # 'price', 'volume', 'spread', 'momentum'
    value: float
    confidence: float
    metadata: Dict[str, Any]

class PerformanceMonitor:
    """性能監控器"""

    def __init__(self):
        self.metrics = {
            "total_processed": 0,
            "avg_latency_ms": 0.0,
            "max_latency_ms": 0.0,
            "min_latency_ms": float('inf'),
            "processing_rate": 0.0,
            "memory_usage_mb": 0.0,
            "cpu_usage_percent": 0.0,
            "queue_size": 0,
            "last_update": datetime.now()
        }
        self.latency_samples = deque(maxlen=1000)
        self.processing_times = deque(maxlen=100)
        self.start_time = time.time()

    def record_latency(self, processing_time: float):
        """記錄處理延遲"""
        latency_ms = processing_time * 1000
        self.latency_samples.append(latency_ms)

        self.metrics["total_processed"] += 1
        self.metrics["max_latency_ms"] = max(self.metrics["max_latency_ms"], latency_ms)
        self.metrics["min_latency_ms"] = min(self.metrics["min_latency_ms"], latency_ms)
        self.metrics["avg_latency_ms"] = np.mean(self.latency_samples)

    def update_system_metrics(self, queue_size: int = 0):
        """更新系統指標"""
        # 計算處理速率
        elapsed_time = time.time() - self.start_time
        self.metrics["processing_rate"] = self.metrics["total_processed"] / elapsed_time

        # 更新資源使用情況
        self.metrics["memory_usage_mb"] = psutil.Process().memory_info().rss / 1024 / 1024
        self.metrics["cpu_usage_percent"] = psutil.cpu_percent()
        self.metrics["queue_size"] = queue_size
        self.metrics["last_update"] = datetime.now()

    def get_metrics(self) -> Dict[str, Any]:
        """獲取性能指標"""
        return {
            **self.metrics,
            "latency_95th_percentile": np.percentile(list(self.latency_samples), 95) if self.latency_samples else 0,
            "latency_99th_percentile": np.percentile(list(self.latency_samples), 99) if self.latency_samples else 0
        }

class DataBuffer:
    """高性能數據緩衝區"""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.buffers = {}  # symbol -> deque
        self.locks = {}     # symbol -> threading.Lock
        self.stats = {
            "total_additions": 0,
            "total_retrievals": 0,
            "buffer_hits": 0,
            "buffer_misses": 0
        }

    def _ensure_buffer(self, symbol: str):
        """確保符號緩衝區存在"""
        if symbol not in self.buffers:
            self.buffers[symbol] = deque(maxlen=self.max_size)
            self.locks[symbol] = threading.Lock()

    def add(self, data_point: MarketDataPoint) -> bool:
        """添加數據點到緩衝區"""
        start_time = time.perf_counter()

        self._ensure_buffer(data_point.symbol)

        with self.locks[data_point.symbol]:
            self.buffers[data_point.symbol].append(data_point)

        self.stats["total_additions"] += 1
        processing_time = time.perf_counter() - start_time
        data_point.processing_time = processing_time

        return processing_time < 0.001  # 返回是否滿足1ms目標

    def get_latest(self, symbol: str, count: int = 1) -> List[MarketDataPoint]:
        """獲取最新的數據點"""
        self._ensure_buffer(symbol)

        with self.locks[symbol]:
            buffer = self.buffers[symbol]
            if not buffer:
                self.stats["buffer_misses"] += 1
                return []

            self.stats["total_retrievals"] += 1
            self.stats["buffer_hits"] += 1

            # 返回最新的count個數據點
            latest_count = min(count, len(buffer))
            return [buffer[-(i + 1)] for i in range(latest_count)]

    def get_range(self, symbol: str, start_time: datetime, end_time: datetime) -> List[MarketDataPoint]:
        """獲取時間範圍內的數據點"""
        self._ensure_buffer(symbol)

        with self.locks[symbol]:
            buffer = self.buffers[symbol]
            return [
                dp for dp in buffer
                if start_time <= dp.timestamp <= end_time
            ]

    def clear_old(self, symbol: str, older_than: datetime):
        """清理舊數據"""
        self._ensure_buffer(symbol)

        with self.locks[symbol]:
            buffer = self.buffers[symbol]
            # 移除早於指定時間的數據
            while buffer and buffer[0].timestamp < older_than:
                buffer.popleft()

    def get_stats(self) -> Dict[str, Any]:
        """獲取緩衝區統計"""
        return {
            **self.stats,
            "buffer_sizes": {symbol: len(buffer) for symbol, buffer in self.buffers.items()},
            "total_symbols": len(self.buffers)
        }

class SignalProcessor:
    """信號處理器"""

    def __init__(self, buffer: DataBuffer):
        self.buffer = buffer
        self.processors = {
            "price_momentum": self._calculate_price_momentum,
            "volume_surge": self._detect_volume_surge,
            "spread_anomaly": self._detect_spread_anomaly,
            "volatility_spike": self._detect_volatility_spike,
            "cross_market_arbitrage": self._detect_arbitrage_opportunities
        }
        self.signal_queue = asyncio.Queue(maxsize=1000)

    async def process_data_point(self, data_point: MarketDataPoint) -> List[ProcessedSignal]:
        """處理單個數據點"""
        signals = []

        # 異步處理各種信號
        for signal_type, processor in self.processors.items():
            try:
                signal = await processor(data_point)
                if signal:
                    signals.append(signal)

                    # 將信號加入隊列
                    try:
                        self.signal_queue.put_nowait(signal)
                    except asyncio.QueueFull:
                        logger.warning(f"Signal queue full, dropping signal: {signal_type}")

            except Exception as e:
                logger.error(f"Error processing {signal_type}: {e}")

        return signals

    async def _calculate_price_momentum(self, data_point: MarketDataPoint) -> Optional[ProcessedSignal]:
        """計算價格動量"""
        # 獲取最近20個數據點
        recent_points = self.buffer.get_latest(data_point.symbol, 20)

        if len(recent_points) < 10:
            return None

        prices = [dp.price for dp in recent_points]
        returns = np.diff(prices) / prices[:-1]

        # 計算動量指標
        momentum_5 = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 else 0
        momentum_10 = (prices[-1] - prices[-10]) / prices[-10] if len(prices) >= 10 else 0

        # 綜合動量分數
        momentum_score = (momentum_5 * 0.7 + momentum_10 * 0.3)

        # 確定信號強度
        confidence = min(abs(momentum_score) * 10, 1.0)

        return ProcessedSignal(
            symbol=data_point.symbol,
            timestamp=data_point.timestamp,
            signal_type="price_momentum",
            value=momentum_score,
            confidence=confidence,
            metadata={
                "momentum_5": momentum_5,
                "momentum_10": momentum_10,
                "recent_returns": returns[-5:].tolist() if len(returns) >= 5 else []
            }
        )

    async def _detect_volume_surge(self, data_point: MarketDataPoint) -> Optional[ProcessedSignal]:
        """檢測交易量激增"""
        recent_points = self.buffer.get_latest(data_point.symbol, 50)

        if len(recent_points) < 20:
            return None

        volumes = [dp.volume for dp in recent_points]
        current_volume = data_point.volume

        # 計算移動平均
        volume_ma20 = np.mean(volumes[-20:])
        volume_ratio = current_volume / volume_ma20 if volume_ma20 > 0 else 1

        # 檢測異常激增（超過3倍平均值）
        if volume_ratio > 3.0:
            confidence = min(volume_ratio / 10, 1.0)

            return ProcessedSignal(
                symbol=data_point.symbol,
                timestamp=data_point.timestamp,
                signal_type="volume_surge",
                value=volume_ratio,
                confidence=confidence,
                metadata={
                    "current_volume": current_volume,
                    "avg_volume_20": volume_ma20,
                    "surge_magnitude": volume_ratio - 1
                }
            )

        return None

    async def _detect_spread_anomaly(self, data_point: MarketDataPoint) -> Optional[ProcessedSignal]:
        """檢測買賣盤異常"""
        spread = data_point.ask - data_point.bid
        spread_ratio = spread / data_point.price if data_point.price > 0 else 0

        # 正常買賣盤比例應該很小（<0.2%）
        if spread_ratio > 0.002:  # 0.2%
            confidence = min(spread_ratio * 100, 1.0)

            return ProcessedSignal(
                symbol=data_point.symbol,
                timestamp=data_point.timestamp,
                signal_type="spread_anomaly",
                value=spread_ratio,
                confidence=confidence,
                metadata={
                    "bid": data_point.bid,
                    "ask": data_point.ask,
                    "spread_bps": spread_ratio * 10000  # 基點
                }
            )

        return None

    async def _detect_volatility_spike(self, data_point: MarketDataPoint) -> Optional[ProcessedSignal]:
        """檢測波動率異常"""
        recent_points = self.buffer.get_latest(data_point.symbol, 30)

        if len(recent_points) < 20:
            return None

        prices = [dp.price for dp in recent_points]
        returns = np.diff(prices) / prices[:-1]

        # 計算當前波動率（滾動標準差）
        current_volatility = np.std(returns[-10:]) if len(returns) >= 10 else 0
        baseline_volatility = np.std(returns[:-10]) if len(returns) > 10 else current_volatility

        if baseline_volatility > 0:
            volatility_ratio = current_volatility / baseline_volatility

            # 檢測波動率激增（超過2倍基線）
            if volatility_ratio > 2.0:
                confidence = min(volatility_ratio / 5, 1.0)

                return ProcessedSignal(
                    symbol=data_point.symbol,
                    timestamp=data_point.timestamp,
                    signal_type="volatility_spike",
                    value=volatility_ratio,
                    confidence=confidence,
                    metadata={
                        "current_volatility": current_volatility,
                        "baseline_volatility": baseline_volatility,
                        "volatility_percent": current_volatility * 100
                    }
                )

        return None

    async def _detect_arbitrage_opportunities(self, data_point: MarketDataPoint) -> Optional[ProcessedSignal]:
        """檢測跨市場套利機會"""
        # 這裡可以檢測不同交易所之間的價格差異
        # 目前簡化實現，可以擴展為真實的多市場套利檢測

        # 模擬檢測A+H股套利
        a_shares = ["00700", "00941", "01398", "03988", "02318"]
        hk_shares = ["0700.HK", "0941.HK", "1398.HK", "3988.HK", "2318.HK"]

        symbol_code = data_point.symbol.replace('.HK', '')

        if symbol_code in a_shares:
            # 模擬檢測H股對應的A股價格
            a_stock_price = data_point.price * 0.9  # 模擬匯率和市場差異
            price_ratio = data_point.price / a_stock_price

            # 檢測套利機會（價格偏離超過5%）
            if abs(price_ratio - 1.0) > 0.05:
                confidence = min(abs(price_ratio - 1.0) * 10, 1.0)

                return ProcessedSignal(
                    symbol=data_point.symbol,
                    timestamp=data_point.timestamp,
                    signal_type="cross_market_arbitrage",
                    value=price_ratio - 1.0,
                    confidence=confidence,
                    metadata={
                        "hk_price": data_point.price,
                        "simulated_a_price": a_stock_price,
                        "price_ratio": price_ratio,
                        "arbitrage_direction": "HK_to_A" if price_ratio > 1 else "A_to_HK"
                    }
                )

        return None

    async def get_signal_stream(self) -> ProcessedSignal:
        """獲取信號流"""
        return await self.signal_queue.get()

    def get_queue_size(self) -> int:
        """獲取信號隊列大小"""
        return self.signal_queue.qsize()

class HighPerformancePipeline:
    """高性能數據處理管道"""

    def __init__(self, num_workers: int = None):
        self.num_workers = num_workers or (mp.cpu_count() // 2)
        self.buffer = DataBuffer(max_size=50000)
        self.processor = SignalProcessor(self.buffer)
        self.performance_monitor = PerformanceMonitor()

        # 輸入和輸出隊列
        self.input_queue = asyncio.Queue(maxsize=10000)
        self.output_queue = asyncio.Queue(maxsize=5000)

        # 線程池
        self.executor = ThreadPoolExecutor(max_workers=self.num_workers)

        # 運行狀態
        self.running = False
        self.workers = []

    async def start(self):
        """啟動管道"""
        self.running = True

        logger.info(f"Starting high-performance pipeline with {self.num_workers} workers")

        # 啟動工作線程
        for i in range(self.num_workers):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.workers.append(worker)

        # 啟動性能監控
        monitor_task = asyncio.create_task(self._monitoring_loop())
        self.workers.append(monitor_task)

        # 啟動垃圾回收
        gc_task = asyncio.create_task(self._gc_loop())
        self.workers.append(gc_task)

        logger.info("High-performance pipeline started successfully")

    async def stop(self):
        """停止管道"""
        self.running = False

        # 等待所有工作線程完成
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)

        # 清理資源
        self.executor.shutdown(wait=True)

        logger.info("High-performance pipeline stopped")

    async def _worker_loop(self, worker_id: str):
        """工作線程循環"""
        logger.info(f"Worker {worker_id} started")

        while self.running:
            try:
                # 獲取輸入數據
                data_point = await asyncio.wait_for(
                    self.input_queue.get(),
                    timeout=1.0
                )

                # 處理數據
                start_time = time.perf_counter()

                # 添加到緩衝區
                buffer_success = self.buffer.add(data_point)

                # 生成信號
                if buffer_success:
                    signals = await self.processor.process_data_point(data_point)

                    # 將結果放入輸出隊列
                    if signals:
                        try:
                            self.output_queue.put_nowait({
                                "data_point": data_point,
                                "signals": signals,
                                "worker_id": worker_id
                            })
                        except asyncio.QueueFull:
                            logger.warning("Output queue full, dropping result")

                # 記錄性能指標
                processing_time = time.perf_counter() - start_time
                self.performance_monitor.record_latency(processing_time)

            except asyncio.TimeoutError:
                continue  # 正常超時，繼續循環
            except Exception as e:
                logger.error(f"Error in worker {worker_id}: {e}")
                await asyncio.sleep(0.1)  # 避免錯誤循環

    async def _monitoring_loop(self):
        """性能監控循環"""
        while self.running:
            try:
                # 更新系統指標
                self.performance_monitor.update_system_metrics(
                    queue_size=self.input_queue.qsize()
                )

                # 定期清理舊數據
                current_time = datetime.now()
                for symbol in list(self.buffer.buffers.keys()):
                    self.buffer.clear_old(symbol, current_time - pd.Timedelta(minutes=30))

                # 記錄性能日誌
                if self.performance_monitor.metrics["total_processed"] % 1000 == 0:
                    metrics = self.performance_monitor.get_metrics()
                    logger.info(f"Performance: {metrics['avg_latency_ms']:.3f}ms avg, "
                              f"{metrics['processing_rate']:.1f} ops/s, "
                              f"Memory: {metrics['memory_usage_mb']:.1f}MB")

                await asyncio.sleep(5)  # 每5秒監控一次

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _gc_loop(self):
        """垃圾回收循環"""
        while self.running:
            try:
                gc.collect()
                await asyncio.sleep(30)  # 每30秒執行一次GC
            except Exception as e:
                logger.error(f"Error in GC loop: {e}")
                await asyncio.sleep(30)

    async def add_data_point(self, data_point: MarketDataPoint):
        """添加數據點到管道"""
        try:
            self.input_queue.put_nowait(data_point)
        except asyncio.QueueFull:
            logger.warning("Input queue full, dropping data point")
            raise

    async def get_processed_data(self) -> Optional[Dict[str, Any]]:
        """獲取處理後的數據"""
        try:
            return await asyncio.wait_for(
                self.output_queue.get(),
                timeout=1.0
            )
        except asyncio.TimeoutError:
            return None

    def get_performance_metrics(self) -> Dict[str, Any]:
        """獲取性能指標"""
        return {
            "pipeline": self.performance_monitor.get_metrics(),
            "buffer": self.buffer.get_stats(),
            "signal_queue_size": self.processor.get_queue_size(),
            "queue_sizes": {
                "input_queue": self.input_queue.qsize(),
                "output_queue": self.output_queue.qsize()
            }
        }

# 使用示例
async def demo_high_performance_pipeline():
    """演示高性能管道"""
    pipeline = HighPerformancePipeline(num_workers=4)

    try:
        # 啟動管道
        await pipeline.start()

        # 模擬數據輸入
        for i in range(100):
            data_point = MarketDataPoint(
                symbol=f"0700.HK",
                timestamp=datetime.now(),
                price=300.0 + np.random.normal(0, 1),
                volume=np.random.randint(1000, 10000),
                bid=299.5 + np.random.normal(0, 0.5),
                ask=300.5 + np.random.normal(0, 0.5),
                source="simulator"
            )

            await pipeline.add_data_point(data_point)
            await asyncio.sleep(0.001)  # 1ms間隔

        # 獲取處理結果
        for _ in range(10):
            result = await pipeline.get_processed_data()
            if result:
                print(f"Processed {len(result['signals'])} signals in "
                      f"{result['data_point'].processing_time * 1000:.3f}ms")

            await asyncio.sleep(0.1)

        # 顯示性能指標
        metrics = pipeline.get_performance_metrics()
        print(f"Final performance metrics: {json.dumps(metrics, indent=2, default=str)}")

    finally:
        await pipeline.stop()

if __name__ == "__main__":
    asyncio.run(demo_high_performance_pipeline())
#!/usr/bin/env python3
"""
Real-time Data Collection Framework - Base Collector
实时数据收集框架 - 基础采集器

提供统一的数据采集接口和基础功能
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
import json
import threading
from queue import Queue, Empty
import hashlib

logger = logging.getLogger(__name__)

class DataSourceStatus(Enum):
    """数据源状态枚举"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"

@dataclass
class DataPoint:
    """统一数据点格式"""
    symbol: str
    timestamp: datetime
    value: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    data_type: str = ""
    quality_score: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'metadata': self.metadata,
            'source': self.source,
            'data_type': self.data_type,
            'quality_score': self.quality_score
        }

    def get_hash(self) -> str:
        """获取数据点哈希值，用于去重"""
        content = f"{self.symbol}_{self.timestamp}_{self.source}"
        return hashlib.md5(content.encode()).hexdigest()

@dataclass
class CollectorMetrics:
    """采集器性能指标"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_data_points: int = 0
    average_response_time: float = 0.0
    last_data_time: Optional[datetime] = None
    uptime_start: datetime = field(default_factory=datetime.now)
    error_count: int = 0
    last_error: Optional[str] = None

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    @property
    def uptime_seconds(self) -> float:
        """运行时间（秒）"""
        return (datetime.now() - self.uptime_start).total_seconds()

    @property
    def data_points_per_second(self) -> float:
        """每秒数据点数量"""
        uptime = self.uptime_seconds
        if uptime == 0:
            return 0.0
        return self.total_data_points / uptime

class BaseCollector(ABC):
    """数据采集器基类"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.status = DataSourceStatus.DISCONNECTED
        self.metrics = CollectorMetrics()
        self.callbacks: List[Callable[[DataPoint], None]] = []

        # 配置参数
        self.request_timeout = config.get('timeout', 30)
        self.retry_attempts = config.get('retry_attempts', 3)
        self.retry_delay = config.get('retry_delay', 1.0)
        self.enable_reconnect = config.get('enable_reconnect', True)
        self.reconnect_interval = config.get('reconnect_interval', 5.0)
        self.max_queue_size = config.get('max_queue_size', 10000)

        # 内部状态
        self._running = False
        self._task = None
        self._data_queue = Queue(maxsize=self.max_queue_size)
        self._error_handlers: List[Callable[[Exception], None]] = []
        self._last_error_time = None

        logger.info(f"Collector '{self.name}' initialized")

    @abstractmethod
    async def connect(self) -> bool:
        """连接数据源"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass

    @abstractmethod
    async def collect_data(self) -> AsyncGenerator[DataPoint, None]:
        """采集数据的异步生成器"""
        pass

    def add_callback(self, callback: Callable[[DataPoint], None]) -> None:
        """添加数据回调函数"""
        if callback not in self.callbacks:
            self.callbacks.append(callback)
            logger.debug(f"Added callback to collector '{self.name}'")

    def remove_callback(self, callback: Callable[[DataPoint], None]) -> None:
        """移除数据回调函数"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            logger.debug(f"Removed callback from collector '{self.name}'")

    def add_error_handler(self, handler: Callable[[Exception], None]) -> None:
        """添加错误处理器"""
        if handler not in self._error_handlers:
            self._error_handlers.append(handler)

    async def start(self) -> None:
        """启动采集器"""
        if self._running:
            logger.warning(f"Collector '{self.name}' is already running")
            return

        logger.info(f"Starting collector '{self.name}'...")
        self._running = True
        self.metrics.uptime_start = datetime.now()

        try:
            # 连接数据源
            self.status = DataSourceStatus.CONNECTING
            connected = await self.connect()

            if not connected:
                self.status = DataSourceStatus.ERROR
                raise ConnectionError(f"Failed to connect to data source '{self.name}'")

            self.status = DataSourceStatus.CONNECTED
            logger.info(f"Collector '{self.name}' connected successfully")

            # 启动数据采集任务
            self._task = asyncio.create_task(self._collection_loop())

        except Exception as e:
            self.status = DataSourceStatus.ERROR
            self._handle_error(e)
            raise

    async def stop(self) -> None:
        """停止采集器"""
        if not self._running:
            return

        logger.info(f"Stopping collector '{self.name}'...")
        self._running = False

        # 取消采集任务
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        # 断开连接
        await self.disconnect()
        self.status = DataSourceStatus.DISCONNECTED

        # 处理队列中剩余数据
        self._process_remaining_data()

        logger.info(f"Collector '{self.name}' stopped")

    async def _collection_loop(self) -> None:
        """主采集循环"""
        logger.info(f"Collection loop started for '{self.name}'")

        try:
            async for data_point in self.collect_data():
                if not self._running:
                    break

                # 更新指标
                self._update_metrics(True)

                # 处理数据点
                await self._process_data_point(data_point)

        except asyncio.CancelledError:
            logger.info(f"Collection loop cancelled for '{self.name}'")
        except Exception as e:
            self.status = DataSourceStatus.ERROR
            self._handle_error(e)

            # 重连逻辑
            if self.enable_reconnect:
                await self._reconnect()
        finally:
            logger.info(f"Collection loop ended for '{self.name}'")

    async def _process_data_point(self, data_point: DataPoint) -> None:
        """处理单个数据点"""
        try:
            # 数据质量验证
            if not self._validate_data_point(data_point):
                logger.warning(f"Invalid data point from '{self.name}': {data_point.symbol}")
                return

            # 添加到队列
            try:
                self._data_queue.put_nowait(data_point)
            except:
                # 队列满了，移除最旧的数据
                try:
                    self._data_queue.get_nowait()
                    self._data_queue.put_nowait(data_point)
                    logger.warning(f"Queue full, dropped old data from '{self.name}'")
                except Empty:
                    pass

            # 通知回调函数
            for callback in self.callbacks:
                try:
                    callback(data_point)
                except Exception as e:
                    logger.error(f"Error in callback for collector '{self.name}': {e}")

            # 更新最后数据时间
            self.metrics.last_data_time = datetime.now()

        except Exception as e:
            logger.error(f"Error processing data point in '{self.name}': {e}")

    def _validate_data_point(self, data_point: DataPoint) -> bool:
        """验证数据点质量"""
        # 基本验证
        if not data_point.symbol or not data_point.timestamp:
            return False

        if data_point.value is None:
            return False

        # 时间戳验证（不能太旧或太新）
        now = datetime.now(timezone.utc)
        if isinstance(data_point.timestamp, str):
            try:
                data_point.timestamp = datetime.fromisoformat(data_point.timestamp.replace('Z', '+00:00'))
            except:
                return False

        # 允许5分钟的时间偏差
        time_diff = abs((now - data_point.timestamp).total_seconds())
        if time_diff > 300:  # 5 minutes
            return False

        # 数值验证
        if isinstance(data_point.value, (int, float)):
            if not (-1e10 <= data_point.value <= 1e10):  # 合理的数值范围
                return False

        return True

    def _update_metrics(self, success: bool) -> None:
        """更新性能指标"""
        self.metrics.total_requests += 1

        if success:
            self.metrics.successful_requests += 1
            self.metrics.total_data_points += 1
        else:
            self.metrics.failed_requests += 1
            self.metrics.error_count += 1

    def _handle_error(self, error: Exception) -> None:
        """处理错误"""
        self.metrics.last_error = str(error)
        self._last_error_time = datetime.now()

        logger.error(f"Error in collector '{self.name}': {error}")

        # 调用错误处理器
        for handler in self._error_handlers:
            try:
                handler(error)
            except Exception as e:
                logger.error(f"Error in error handler for '{self.name}': {e}")

    async def _reconnect(self) -> None:
        """重连逻辑"""
        if not self.enable_reconnect:
            return

        reconnect_count = 0
        max_reconnects = self.config.get('max_reconnect_attempts', 10)

        while self._running and reconnect_count < max_reconnects:
            reconnect_count += 1
            logger.info(f"Reconnect attempt {reconnect_count}/{max_reconnects} for '{self.name}'")

            self.status = DataSourceStatus.RECONNECTING

            try:
                # 等待重连间隔
                await asyncio.sleep(self.reconnect_interval)

                # 尝试重连
                if await self.connect():
                    self.status = DataSourceStatus.CONNECTED
                    logger.info(f"Successfully reconnected collector '{self.name}'")

                    # 重新启动采集循环
                    if not self._task or self._task.done():
                        self._task = asyncio.create_task(self._collection_loop())

                    return
                else:
                    logger.warning(f"Reconnect failed for '{self.name}', attempt {reconnect_count}")

            except Exception as e:
                logger.error(f"Reconnect error for '{self.name}': {e}")
                self._handle_error(e)

        # 超过最大重连次数
        self.status = DataSourceStatus.ERROR
        logger.error(f"Max reconnect attempts reached for '{self.name}', stopping")

    def _process_remaining_data(self) -> None:
        """处理队列中剩余的数据"""
        processed = 0
        while not self._data_queue.empty():
            try:
                data_point = self._data_queue.get_nowait()
                for callback in self.callbacks:
                    try:
                        callback(data_point)
                    except:
                        pass
                processed += 1
            except Empty:
                break

        if processed > 0:
            logger.info(f"Processed {processed} remaining data points from '{self.name}'")

    def get_status(self) -> Dict[str, Any]:
        """获取采集器状态"""
        return {
            'name': self.name,
            'status': self.status.value,
            'running': self._running,
            'queue_size': self._data_queue.qsize(),
            'metrics': {
                'total_requests': self.metrics.total_requests,
                'successful_requests': self.metrics.successful_requests,
                'failed_requests': self.metrics.failed_requests,
                'success_rate': self.metrics.success_rate,
                'total_data_points': self.metrics.total_data_points,
                'data_points_per_second': self.metrics.data_points_per_second,
                'uptime_seconds': self.metrics.uptime_seconds,
                'last_data_time': self.metrics.last_data_time.isoformat() if self.metrics.last_data_time else None,
                'error_count': self.metrics.error_count,
                'last_error': self.metrics.last_error
            }
        }

    async def health_check(self) -> bool:
        """健康检查"""
        if not self._running:
            return False

        # 检查最近是否有数据
        if self.metrics.last_data_time:
            time_since_last_data = (datetime.now() - self.metrics.last_data_time).total_seconds()
            if time_since_last_data > 60:  # 60秒无数据认为不健康
                return False

        # 检查成功率
        if self.metrics.success_rate < 0.8 and self.metrics.total_requests > 10:
            return False

        return True

# 便利函数
def create_data_point(symbol: str, value: Any, source: str,
                     data_type: str = "", metadata: Dict[str, Any] = None,
                     timestamp: datetime = None) -> DataPoint:
    """创建数据点的便利函数"""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    if metadata is None:
        metadata = {}

    return DataPoint(
        symbol=symbol,
        timestamp=timestamp,
        value=value,
        metadata=metadata,
        source=source,
        data_type=data_type
    )
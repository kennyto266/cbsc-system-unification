#!/usr / bin / env python3
"""
Simplified System - Event Processor
简化系统 - 事件处理器

高性能实时事件处理引擎
High - performance real - time event processing engine
"""

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型枚举"""

    PRICE_UPDATE = "price_update"
    INDICATOR_UPDATE = "indicator_update"
    TECHNICAL_SIGNAL = "technical_signal"
    MARKET_EVENT = "market_event"
    RISK_ALERT = "risk_alert"
    SYSTEM_EVENT = "system_event"
    CUSTOM = "custom"


class EventPriority(Enum):
    """事件优先级枚举"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    """事件数据结构"""

    id: str
    type: EventType
    priority: EventPriority = EventPriority.NORMAL
    timestamp: datetime = field(default_factory = datetime.now)
    symbol: Optional[str] = None
    data: Dict[str, Any] = field(default_factory = dict)
    source: Optional[str] = None
    correlation_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "data": self.data,
            "source": self.source,
            "correlation_id": self.correlation_id,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }


class EventFilter:
    """事件过滤器"""

    def __init__(
        self,
        event_types: Optional[Set[EventType]] = None,
        symbols: Optional[Set[str]] = None,
        priorities: Optional[Set[EventPriority]] = None,
        custom_filter: Optional[Callable[[Event], bool]] = None,
    ):
        self.event_types = event_types or set()
        self.symbols = symbols or set()
        self.priorities = priorities or set()
        self.custom_filter = custom_filter

    def matches(self, event: Event) -> bool:
        """检查事件是否匹配过滤器"""
        # 检查事件类型
        if self.event_types and event.type not in self.event_types:
            return False

        # 检查股票代码
        if self.symbols and event.symbol not in self.symbols:
            return False

        # 检查优先级
        if self.priorities and event.priority not in self.priorities:
            return False

        # 自定义过滤器
        if self.custom_filter and not self.custom_filter(event):
            return False

        return True


class EventHandler:
    """事件处理器"""

    def __init__(
        self,
        handler_id: str,
        handler_func: Callable[[Event], Any],
        filter: Optional[EventFilter] = None,
        async_handler: bool = False,
        retry_on_failure: bool = True,
    ):
        self.handler_id = handler_id
        self.handler_func = handler_func
        self.filter = filter
        self.async_handler = async_handler
        self.retry_on_failure = retry_on_failure

        # 统计信息
        self.processed_count = 0
        self.error_count = 0
        self.last_processed = None
        self.average_processing_time = 0.0

    async def handle_event(self, event: Event) -> bool:
        """
        处理事件

        Returns:
            bool: 处理是否成功
        """
        # 检查过滤器
        if self.filter and not self.filter.matches(event):
            return True  # 过滤掉的事件也算成功处理

        start_time = time.time()

        try:
            # 调用处理函数
            if self.async_handler:
                await self.handler_func(event)
            else:
                self.handler_func(event)

            # 更新统计信息
            self.processed_count += 1
            self.last_processed = datetime.now()

            processing_time = time.time() - start_time
            self.average_processing_time = (
                self.average_processing_time * (self.processed_count - 1)
                + processing_time
            ) / self.processed_count

            logger.debug(
                f"Handler {self.handler_id} processed event {event.id} in {processing_time:.4f}s"
            )
            return True

        except Exception as e:
            self.error_count += 1
            logger.error(
                f"Handler {self.handler_id} failed to process event {event.id}: {e}"
            )

            if self.retry_on_failure and event.retry_count < event.max_retries:
                event.retry_count += 1
                logger.info(f"Retrying event {event.id}, attempt {event.retry_count}")
                return False  # 返回False表示需要重试

            return True  # 达到最大重试次数，标记为已处理

    def get_stats(self) -> Dict[str, Any]:
        """获取处理器统计信息"""
        return {
            "handler_id": self.handler_id,
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(1, self.processed_count),
            "last_processed": (
                self.last_processed.isoformat() if self.last_processed else None
            ),
            "average_processing_time": self.average_processing_time,
        }


class EventQueue:
    """优先级事件队列"""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._queues = {priority: deque() for priority in EventPriority}
        self._total_size = 0
        self._lock = asyncio.Lock()

    async def put(self, event: Event) -> bool:
        """添加事件到队列"""
        async with self._lock:
            if self._total_size >= self.max_size:
                # 队列满时，移除最旧的低优先级事件
                removed = await self._remove_oldest_low_priority()
                if not removed:
                    logger.warning(
                        "Event queue is full and no low priority events to remove"
                    )
                    return False

            self._queues[event.priority].append(event)
            self._total_size += 1
            return True

    async def get(self) -> Optional[Event]:
        """从队列获取事件（按优先级）"""
        async with self._lock:
            for priority in sorted(EventPriority, key = lambda x: x.value, reverse = True):
                if self._queues[priority]:
                    event = self._queues[priority].popleft()
                    self._total_size -= 1
                    return event

            return None

    async def _remove_oldest_low_priority(self) -> bool:
        """移除最旧的低优先级事件"""
        for priority in sorted(EventPriority, key = lambda x: x.value):
            if self._queues[priority]:
                self._queues[priority].popleft()
                self._total_size -= 1
                return True
        return False

    def size(self) -> int:
        """获取队列大小"""
        return self._total_size

    def size_by_priority(self) -> Dict[str, int]:
        """按优先级获取队列大小"""
        return {priority.name: len(queue) for priority, queue in self._queues.items()}


class EventProcessor:
    """
    高性能实时事件处理引擎
    支持优先级队列、事件过滤、异步处理和性能监控
    """

    def __init__(self, max_workers: int = 10, queue_size: int = 10000):
        self.max_workers = max_workers
        self.event_queue = EventQueue(max_size = queue_size)
        self.handlers: Dict[str, EventHandler] = {}
        self.retry_queue: deque = deque()

        # 运行状态
        self._running = False
        self._workers: List[asyncio.Task] = []
        self._retry_worker: Optional[asyncio.Task] = None

        # 统计信息
        self.stats = {
            "events_processed": 0,
            "events_failed": 0,
            "events_queued": 0,
            "start_time": None,
            "average_processing_time": 0.0,
        }

        # 性能监控
        self.performance_history = deque(maxlen = 1000)  # 保留最近1000个事件的处理时间

        logger.info(f"Event processor initialized with {max_workers} workers")

    async def start(self) -> None:
        """启动事件处理器"""
        if self._running:
            logger.warning("Event processor is already running")
            return

        self._running = True
        self.stats["start_time"] = datetime.now()

        logger.info("Starting event processor...")

        # 启动工作线程
        self._workers = [
            asyncio.create_task(self._worker(f"worker_{i}"))
            for i in range(self.max_workers)
        ]

        # 启动重试工作线程
        self._retry_worker = asyncio.create_task(self._retry_worker())

        logger.info(f"Event processor started with {len(self._workers)} workers")

    async def stop(self) -> None:
        """停止事件处理器"""
        if not self._running:
            return

        self._running = False

        logger.info("Stopping event processor...")

        # 取消所有工作任务
        for worker in self._workers:
            worker.cancel()

        # 取消重试任务
        if self._retry_worker:
            self._retry_worker.cancel()

        # 等待任务完成
        await asyncio.gather(*self._workers, self._retry_worker, return_exceptions = True)

        logger.info("Event processor stopped")

    async def _worker(self, worker_id: str) -> None:
        """工作线程主循环"""
        logger.info(f"Worker {worker_id} started")

        while self._running:
            try:
                # 从队列获取事件
                event = await asyncio.wait_for(self.event_queue.get(), timeout = 1.0)
                if event is None:
                    continue

                # 处理事件
                success = await self._process_event(event)

                # 更新统计信息
                if success:
                    self.stats["events_processed"] += 1
                else:
                    self.stats["events_failed"] += 1
                    # 如果处理失败且需要重试，添加到重试队列
                    if event.retry_count < event.max_retries:
                        self.retry_queue.append(event)

            except asyncio.TimeoutError:
                continue  # 超时继续等待
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(0.1)  # 错误后短暂休息

        logger.info(f"Worker {worker_id} stopped")

    async def _retry_worker(self) -> None:
        """重试工作线程"""
        logger.info("Retry worker started")

        while self._running:
            try:
                if self.retry_queue:
                    event = self.retry_queue.popleft()

                    # 添加延迟后重新放入主队列
                    await asyncio.sleep(
                        min(event.retry_count * 2, 30)
                    )  # 指数退避，最大30秒
                    await self.publish_event(event)
                else:
                    await asyncio.sleep(1.0)  # 没有重试事件时等待

            except Exception as e:
                logger.error(f"Retry worker error: {e}")
                await asyncio.sleep(1.0)

        logger.info("Retry worker stopped")

    async def _process_event(self, event: Event) -> bool:
        """处理单个事件"""
        start_time = time.time()
        overall_success = True

        # 并行调用所有匹配的处理器
        tasks = []
        for handler in self.handlers.values():
            task = asyncio.create_task(handler.handle_event(event))
            tasks.append(task)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions = True)

            # 检查结果
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Handler error: {result}")
                    overall_success = False
                elif not result:
                    overall_success = False

        # 记录性能
        processing_time = time.time() - start_time
        self.performance_history.append(processing_time)
        self._update_average_processing_time(processing_time)

        return overall_success

    def _update_average_processing_time(self, processing_time: float) -> None:
        """更新平均处理时间"""
        if self.stats["events_processed"] == 0:
            self.stats["average_processing_time"] = processing_time
        else:
            total_events = self.stats["events_processed"]
            current_avg = self.stats["average_processing_time"]
            self.stats["average_processing_time"] = (
                current_avg * total_events + processing_time
            ) / (total_events + 1)

    async def publish_event(self, event: Event) -> bool:
        """
        发布事件

        Args:
            event: 要发布的事件

        Returns:
            bool: 是否成功加入队列
        """
        success = await self.event_queue.put(event)
        if success:
            self.stats["events_queued"] += 1
            logger.debug(f"Event {event.id} queued successfully")
        else:
            logger.warning(f"Failed to queue event {event.id}")

        return success

    def create_event(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        symbol: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        source: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Event:
        """
        创建事件

        Args:
            event_type: 事件类型
            data: 事件数据
            symbol: 股票代码
            priority: 优先级
            source: 事件源
            correlation_id: 关联ID

        Returns:
            Event: 创建的事件
        """
        event_id = f"{event_type.value}_{int(time.time() * 1000000)}"

        return Event(
            id = event_id,
            type = event_type,
            priority = priority,
            symbol = symbol,
            data = data,
            source = source,
            correlation_id = correlation_id,
        )

    async def publish_price_update(
        self, symbol: str, price: float, volume: int = 0, source: Optional[str] = None
    ) -> bool:
        """发布价格更新事件"""
        data = {
            "price": price,
            "volume": volume,
            "timestamp": datetime.now().isoformat(),
        }

        event = self.create_event(
            EventType.PRICE_UPDATE,
            data,
            symbol = symbol,
            priority = EventPriority.NORMAL,
            source = source,
        )

        return await self.publish_event(event)

    async def publish_technical_signal(
        self,
        symbol: str,
        signal_type: str,
        signal_value: float,
        confidence: float,
        source: Optional[str] = None,
    ) -> bool:
        """发布技术信号事件"""
        data = {
            "signal_type": signal_type,
            "signal_value": signal_value,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        }

        event = self.create_event(
            EventType.TECHNICAL_SIGNAL,
            data,
            symbol = symbol,
            priority = EventPriority.HIGH,
            source = source,
        )

        return await self.publish_event(event)

    async def publish_risk_alert(
        self,
        symbol: str,
        alert_type: str,
        alert_level: str,
        message: str,
        source: Optional[str] = None,
    ) -> bool:
        """发布风险警报事件"""
        data = {
            "alert_type": alert_type,
            "alert_level": alert_level,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }

        event = self.create_event(
            EventType.RISK_ALERT,
            data,
            symbol = symbol,
            priority = EventPriority.CRITICAL,
            source = source,
        )

        return await self.publish_event(event)

    def register_handler(
        self,
        handler_id: str,
        handler_func: Callable[[Event], Any],
        filter: Optional[EventFilter] = None,
        async_handler: bool = False,
    ) -> None:
        """
        注册事件处理器

        Args:
            handler_id: 处理器ID
            handler_func: 处理函数
            filter: 事件过滤器
            async_handler: 是否为异步处理器
        """
        if handler_id in self.handlers:
            logger.warning(f"Handler {handler_id} already exists, overwriting...")

        self.handlers[handler_id] = EventHandler(
            handler_id = handler_id,
            handler_func = handler_func,
            filter = filter,
            async_handler = async_handler,
        )

        logger.info(f"Registered event handler: {handler_id}")

    def unregister_handler(self, handler_id: str) -> None:
        """取消注册事件处理器"""
        if handler_id in self.handlers:
            del self.handlers[handler_id]
            logger.info(f"Unregistered event handler: {handler_id}")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()

        handler_stats = {
            handler_id: handler.get_stats()
            for handler_id, handler in self.handlers.items()
        }

        return {
            **self.stats,
            "uptime_seconds": uptime,
            "queue_size": self.event_queue.size(),
            "queue_size_by_priority": self.event_queue.size_by_priority(),
            "retry_queue_size": len(self.retry_queue),
            "handler_count": len(self.handlers),
            "worker_count": len(self._workers),
            "handler_stats": handler_stats,
            "performance_history_size": len(self.performance_history),
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        if not self.performance_history:
            return {}

        processing_times = list(self.performance_history)

        return {
            "average_processing_time": np.mean(processing_times),
            "median_processing_time": np.median(processing_times),
            "p95_processing_time": np.percentile(processing_times, 95),
            "p99_processing_time": np.percentile(processing_times, 99),
            "min_processing_time": np.min(processing_times),
            "max_processing_time": np.max(processing_times),
            "std_processing_time": np.std(processing_times),
            "events_per_second": self.stats["events_processed"] / max(1, uptime or 1),
        }


# 全局事件处理器实例
_event_processor = None


def get_event_processor() -> EventProcessor:
    """获取全局事件处理器实例"""
    global _event_processor
    if _event_processor is None:
        _event_processor = EventProcessor()
    return _event_processor


if __name__ == "__main__":

    async def test_event_processor():
        """测试事件处理器"""
        processor = EventProcessor(max_workers = 3)

        # 定义测试处理器
        def price_handler(event: Event):
            print(f"Price update: {event.symbol} - ${event.data['price']}")
            time.sleep(0.1)  # 模拟处理时间

        async def signal_handler(event: Event):
            print(f"Technical signal: {event.symbol} - {event.data['signal_type']}")
            await asyncio.sleep(0.05)

        # 注册处理器
        price_filter = EventFilter(event_types={EventType.PRICE_UPDATE})
        processor.register_handler("price_handler", price_handler, price_filter)

        signal_filter = EventFilter(event_types={EventType.TECHNICAL_SIGNAL})
        processor.register_handler("signal_handler", signal_handler, async_handler = True)

        # 启动处理器
        await processor.start()

        # 发布测试事件
        for i in range(10):
            await processor.publish_price_update("0700.HK", 300.0 + i, source="test")
            await processor.publish_technical_signal(
                "0700.HK", "BUY", 0.8, 0.9, source="test"
            )
            await asyncio.sleep(0.1)

        # 等待处理完成
        await asyncio.sleep(2)

        # 打印统计信息
        stats = processor.get_stats()
        performance = processor.get_performance_metrics()

        print(f"Stats: {stats}")
        print(f"Performance: {performance}")

        # 停止处理器
        await processor.stop()

    # 运行测试
    asyncio.run(test_event_processor())

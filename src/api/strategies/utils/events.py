"""
事件总线系统
Event Bus System

职责：
- 事件发布和订阅
- 异步事件处理
- 系统解耦
"""

import asyncio
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
import json
import logging
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """事件类型枚举"""
    STRATEGY_CREATED = "strategy.created"
    STRATEGY_UPDATED = "strategy.updated"
    STRATEGY_DELETED = "strategy.deleted"
    STRATEGY_EXECUTION_STARTED = "strategy.execution.started"
    STRATEGY_EXECUTION_COMPLETED = "strategy.execution.completed"
    STRATEGY_EXECUTION_FAILED = "strategy.execution.failed"
    SIGNAL_GENERATED = "signal.generated"
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    CACHE_UPDATED = "cache.updated"
    ERROR_OCCURRED = "error.occurred"
    SYSTEM_ALERT = "system.alert"


@dataclass
class Event:
    """事件数据类"""
    event_type: EventType
    data: Dict[str, Any]
    timestamp: datetime
    source: str
    user_id: Optional[int] = None
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_type": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "user_id": self.user_id,
            "correlation_id": self.correlation_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """从字典创建事件"""
        return cls(
            event_type=EventType(data["event_type"]),
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source=data["source"],
            user_id=data.get("user_id"),
            correlation_id=data.get("correlation_id")
        )


class EventBus:
    """事件总线"""

    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._running = False

    def subscribe(self, event_type: EventType, handler: Callable) -> str:
        """
        订阅事件

        Args:
            event_type: 事件类型
            handler: 事件处理函数

        Returns:
            str: 订阅ID
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        subscription_id = f"{event_type.value}_{len(self._subscribers[event_type])}"
        self._subscribers[event_type].append({
            "id": subscription_id,
            "handler": handler
        })

        logger.info(f"订阅事件: {event_type.value}, 处理器ID: {subscription_id}")
        return subscription_id

    def unsubscribe(self, event_type: EventType, subscription_id: str) -> bool:
        """
        取消订阅

        Args:
            event_type: 事件类型
            subscription_id: 订阅ID

        Returns:
            bool: 是否成功取消
        """
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                sub for sub in self._subscribers[event_type]
                if sub["id"] != subscription_id
            ]
            logger.info(f"取消订阅事件: {event_type.value}, 处理器ID: {subscription_id}")
            return True
        return False

    async def publish(self, event: Event) -> int:
        """
        发布事件

        Args:
            event: 事件对象

        Returns:
            int: 处理器数量
        """
        # 记录事件历史
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        logger.info(f"发布事件: {event.event_type.value}, 来源: {event.source}")

        # 获取订阅者
        subscribers = self._subscribers.get(event.event_type, [])
        handler_count = 0

        # 异步调用所有处理器
        tasks = []
        for subscriber in subscribers:
            try:
                task = asyncio.create_task(
                    self._call_handler(subscriber["handler"], event)
                )
                tasks.append(task)
                handler_count += 1
            except Exception as e:
                logger.error(f"创建处理器任务失败: {e}")

        # 等待所有处理器完成
        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"执行事件处理器失败: {e}")

        return handler_count

    async def _call_handler(self, handler: Callable, event: Event):
        """
        调用事件处理器

        Args:
            handler: 处理器函数
            event: 事件对象
        """
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            logger.error(f"事件处理器执行失败: {e}")
            # 发布错误事件
            error_event = Event(
                event_type=EventType.ERROR_OCCURRED,
                data={
                    "error": str(e),
                    "original_event": event.to_dict()
                },
                timestamp=datetime.utcnow(),
                source="event_bus",
                user_id=event.user_id
            )
            await self.publish(error_event)

    def get_event_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        获取事件历史

        Args:
            event_type: 事件类型过滤
            limit: 返回数量限制

        Returns:
            List[Event]: 事件列表
        """
        events = self._event_history

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]

    def get_subscriber_count(self, event_type: Optional[EventType] = None) -> int:
        """
        获取订阅者数量

        Args:
            event_type: 事件类型

        Returns:
            int: 订阅者数量
        """
        if event_type:
            return len(self._subscribers.get(event_type, []))
        else:
            return sum(len(subs) for subs in self._subscribers.values())

    async def clear_history(self, before: Optional[datetime] = None):
        """
        清理事件历史

        Args:
            before: 清理此时间之前的事件
        """
        if before:
            self._event_history = [
                e for e in self._event_history if e.timestamp >= before
            ]
        else:
            self._event_history.clear()

        logger.info(f"清理事件历史完成，保留 {len(self._event_history)} 条记录")


# 全局事件总线实例
event_bus = EventBus()


# 事件处理装饰器
def event_handler(event_type: EventType):
    """
    事件处理装饰器

    Args:
        event_type: 事件类型
    """
    def decorator(func):
        # 自动注册处理器
        subscription_id = event_bus.subscribe(event_type, func)

        # 添加订阅ID到函数属性
        func._event_subscription_id = subscription_id
        func._event_type = event_type

        return func

    return decorator


# 便捷的事件发布函数
async def publish_strategy_event(
    event_type: EventType,
    strategy_id: str,
    data: Dict[str, Any],
    user_id: Optional[int] = None,
    source: str = "strategy_service"
) -> int:
    """
    发布策略相关事件

    Args:
        event_type: 事件类型
        strategy_id: 策略ID
        data: 事件数据
        user_id: 用户ID
        source: 事件来源

    Returns:
        int: 处理器数量
    """
    event = Event(
        event_type=event_type,
        data={**data, "strategy_id": strategy_id},
        timestamp=datetime.utcnow(),
        source=source,
        user_id=user_id
    )
    return await event_bus.publish(event)


async def publish_user_event(
    event_type: EventType,
    user_id: int,
    data: Dict[str, Any],
    source: str = "user_service"
) -> int:
    """
    发布用户相关事件

    Args:
        event_type: 事件类型
        user_id: 用户ID
        data: 事件数据
        source: 事件来源

    Returns:
        int: 处理器数量
    """
    event = Event(
        event_type=event_type,
        data={**data, "user_id": user_id},
        timestamp=datetime.utcnow(),
        source=source,
        user_id=user_id
    )
    return await event_bus.publish(event)


async def publish_system_event(
    event_type: EventType,
    data: Dict[str, Any],
    source: str = "system",
    correlation_id: Optional[str] = None
) -> int:
    """
    发布系统事件

    Args:
        event_type: 事件类型
        data: 事件数据
        source: 事件来源
        correlation_id: 关联ID

    Returns:
        int: 处理器数量
    """
    event = Event(
        event_type=event_type,
        data=data,
        timestamp=datetime.utcnow(),
        source=source,
        correlation_id=correlation_id
    )
    return await event_bus.publish(event)


# 批量事件发布
async def publish_batch_events(events: List[Event]) -> int:
    """
    批量发布事件

    Args:
        events: 事件列表

    Returns:
        int: 总处理器调用次数
    """
    total_handlers = 0
    for event in events:
        total_handlers += await event_bus.publish(event)
    return total_handlers
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Event Bus 系統 - 解耦組件間通信
實現發布-訂閱模式，支持異步事件處理

Architecture Goal: 解耦業務邏輯，提高可擴展性
Performance Goal: 異步處理，非阻塞事件傳遞
"""

import asyncio
import logging
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid

logger = logging.getLogger__name__

class EventPriorityEnum:
"""事件優先級"""
LOW = 1
NORMAL = 2
HIGH = 3
CRITICAL = 4

@dataclass
class Event:
"""事件基類"""
event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
event_type: str = ""
timestamp: datetime = fielddefault_factory=datetime.now
source: str = ""
data: Dict[str, Any] = fielddefault_factory=dict
priority: EventPriority = EventPriority.NORMAL
metadata: Dict[str, Any] = fielddefault_factory=dict

def to_dictself -> Dict[str, Any]:
"""轉換為字典"""
return {
'event_id': self.event_id,
'event_type': self.event_type,
'timestamp': self.timestamp.isoformat(),
'source': self.source,
'data': self.data,
'priority': self.priority.value,
'metadata': self.metadata
}

@dataclass
class EventHandler:
"""事件處理器"""
handler_id: str
callback: Callable
event_type: str
source_filter: Optional[str] = None
priority: EventPriority = EventPriority.NORMAL
async_handler: bool = False
enabled: bool = True

class EventStore:
"""事件存儲"""
def __init__self, max_events: int = 10000:    self.max_events = max_events
self._events: List[Event] = []
self._lock = threading.Lock()

def add_eventself, event: Event:
"""添加事件"""
with self._lock:
self._events.appendevent

if lenself._events > self.max_events:    self._events = self._events[-self.max_events:]

def get_events(self, event_type: str = None, source: str = None,
start_time: datetime = None, end_time: datetime = None,
limit: int = None) -> List[Event]:
"""獲取事件"""
with self._lock:    events = self._events.copy()

if event_type:    events = [e for e in events if e.event_type == event_type]
if source:    events = [e for e in events if e.source == source]
if start_time:    events = [e for e in events if e.timestamp >= start_time]
if end_time:    events = [e for e in events if e.timestamp <= end_time]

if limit:    events = events[-limit:]

return events

def clear_eventsself, older_than: datetime = None:
"""清除事件"""
with self._lock:
if older_than:    self._events = [e for e in self._events if e.timestamp >= older_than]
else:
self._events.clear()

class EventBus:
"""事件總線"""

def __init__(self, enable_persistence: bool = False,
event_store_file: str = "events.json"):    self._handlers: Dict[str, List[EventHandler]] = {}
self._global_handlers: List[EventHandler] = []
self._event_store = EventStore()
self._enable_persistence = enable_persistence
self._event_store_file = event_store_file
self._lock = asyncio.Lock()
self._running = False
self._background_tasks: Set[asyncio.Task] = set()

self._stats = {
'events_published': 0,
'events_processed': 0,
'handlers_registered': 0,
'errors': 0
}

def subscribe(self, event_type: str, handler: Callable,
source_filter: str = None, priority: EventPriority = EventPriority.NORMAL,
handler_id: str = None, async_handler: bool = False) -> str:
"""訂閱事件"""
handler_id = handler_id or str(uuid.uuid4())

event_handler = EventHandler(
handler_id=handler_id,
callback=handler,
event_type=event_type,
source_filter=source_filter,
priority=priority,
async_handler=async_handler
)

if event_type not in self._handlers:    self._handlers[event_type] = []

self._handlers[event_type].appendevent_handler
self._stats['handlers_registered'] += 1

logger.infof"Subscribed handler {handler_id} to event {event_type}"
return handler_id

def unsubscribeself, event_type: str, handler_id: str:
"""取消訂閱"""
if event_type in self._handlers:    self._handlers[event_type] = [
h for h in self._handlers[event_type] if h.handler_id != handler_id
]
logger.infof"Unsubscribed handler {handler_id} from event {event_type}"

def subscribe_all(self, handler: Callable, priority: EventPriority = EventPriority.NORMAL,
handler_id: str = None, async_handler: bool = False) -> str:
"""訂閱所有事件"""
handler_id = handler_id or str(uuid.uuid4())

event_handler = EventHandler(
handler_id=handler_id,
callback=handler,
event_type="*", # 所有事件
priority=priority,
async_handler=async_handler
)

self._global_handlers.appendevent_handler
self._stats['handlers_registered'] += 1

logger.infof"Subscribed global handler {handler_id}"
return handler_id

async def publishself, event: Event -> bool:
"""發布事件（異步）"""
try:    self._stats['events_published'] += 1

self._event_store.add_eventevent

handlers = []

# 特定事件類型的處理器
if event.event_type in self._handlers:
handlers.extendself._handlers[event.event_type]

handlers.extendself._global_handlers

handlers.sortkey=lambda h: h.priority.value, reverse=True

filtered_handlers = [
h for h in handlers
if h.enabled and not h.source_filter or h.source_filter == event.source
]

if not filtered_handlers:
logger.debugf"No handlers for event {event.event_type}"
return True

tasks = []
for handler in filtered_handlers:
if handler.async_handler:    task = asyncio.create_task(self._handle_event_async(handler, event))
else:    task = asyncio.create_task(self._handle_event_sync(handler, event))
tasks.appendtask

# 等待所有處理器完成（非阻塞）
for task in tasks:
self._background_tasks.addtask
task.add_done_callbackself._background_tasks.discard

logger.debug(f"Published event {event.event_type} to {lenfiltered_handlers} handlers")
return True

except Exception as e:    self._stats['errors'] += 1
logger.errorf"Failed to publish event {event.event_type}: {e}"
return False

def publish_syncself, event: Event -> bool:
"""發布事件（同步）"""
try:    self._stats['events_published'] += 1

self._event_store.add_eventevent

# 獲取並處理處理器
handlers = []

if event.event_type in self._handlers:
handlers.extendself._handlers[event.event_type]

handlers.extendself._global_handlers
handlers.sortkey=lambda h: h.priority.value, reverse=True

filtered_handlers = [
h for h in handlers
if h.enabled and not h.source_filter or h.source_filter == event.source
]

for handler in filtered_handlers:
try:
if handler.async_handler:
# 異步處理器，在新線程中運行
loop = asyncio.new_event_loop()
asyncio.set_event_looploop
loop.run_until_complete(self._handle_event_asynchandler, event)
loop.close()
else:
self._handle_event_synchandler, event
except Exception as e:
logger.errorf"Handler {handler.handler_id} failed: {e}"
self._stats['errors'] += 1

return True

except Exception as e:    self._stats['errors'] += 1
logger.errorf"Failed to publish event {event.event_type}: {e}"
return False

async def _handle_event_asyncself, handler: EventHandler, event: Event:
"""處理異步事件"""
try:
await handler.callbackevent
self._stats['events_processed'] += 1
except Exception as e:
logger.errorf"Async handler {handler.handler_id} failed: {e}"
self._stats['errors'] += 1

async def _handle_event_syncself, handler: EventHandler, event: Event:
"""處理同步事件"""
try:
if asyncio.iscoroutinefunctionhandler.callback:
await handler.callbackevent
else:
handler.callbackevent
self._stats['events_processed'] += 1
except Exception as e:
logger.errorf"Sync handler {handler.handler_id} failed: {e}"
self._stats['errors'] += 1

def get_statisticsself -> Dict[str, Any]:
"""獲取統計信息"""
return {
**self._stats,
'active_handlers': sum(lenhandlers for handlers in self._handlers.values()),
'global_handlers': lenself._global_handlers,
'background_tasks': lenself._background_tasks,
'event_store_size': lenself._event_store._events
}

def get_event_history(self, event_type: str = None, source: str = None,
limit: int = 100) -> List[Event]:
"""獲取事件歷史"""
return self._event_store.get_eventsevent_type, source, limit=limit

def clear_event_historyself, older_than_hours: int = 24:
"""清除事件歷史"""
older_than = datetime.now().timestamp() - older_than_hours * 3600
cutoff_time = datetime.fromtimestampolder_than
self._event_store.clear_eventscutoff_time
logger.infof"Cleared events older than {older_than_hours} hours"

def start_background_processingself:
"""啟動後台處理"""
self._running = True
logger.info"Event bus background processing started"

def stop_background_processingself:
"""停止後台處理"""
self._running = False
for task in self._background_tasks:
task.cancel()
logger.info"Event bus background processing stopped"

# 全局事件總線實例
_global_event_bus: Optional[EventBus] = None

def get_event_bus() -> EventBus:
"""獲取全局事件總線"""
global _global_event_bus
if not _global_event_bus:    _global_event_bus = EventBus()
return _global_event_bus

def set_event_busevent_bus: EventBus:
"""設置全局事件總線"""
global _global_event_bus
_global_event_bus = event_bus

def event_handler(event_type: str, source_filter: str = None,
priority: EventPriority = EventPriority.NORMAL, async_handler: bool = False):
"""事件處理器裝飾器"""
def decoratorfunc:    bus = get_event_bus()
bus.subscribeevent_type, func, source_filter, priority, async_handler=async_handler
return func
return decorator

def publish_event(event_type: str, data: Dict[str, Any] = None,
source: str = "", priority: EventPriority = EventPriority.NORMAL):
"""發布事件裝飾器"""
def decoratorfunc:
def wrapper*args, **kwargs:    result = func(*args, **kwargs)
event = Event(
event_type=event_type,
data=data or {},
source=source,
priority=priority
)
bus = get_event_bus()
bus.publish_syncevent
return result
return wrapper
return decorator

class EventTypes:
"""預定義事件類型"""
STRATEGY_CREATED = "strategy.created"
STRATEGY_UPDATED = "strategy.updated"
STRATEGY_DELETED = "strategy.deleted"
STRATEGY_EXECUTION_STARTED = "strategy.execution.started"
STRATEGY_EXECUTION_COMPLETED = "strategy.execution.completed"
STRATEGY_EXECUTION_FAILED = "strategy.execution.failed"

PERFORMANCE_ALERT = "performance.alert"
RISK_ALERT = "risk.alert"
SYSTEM_ERROR = "system.error"
SYSTEM_WARNING = "system.warning"

DATA_UPDATED = "data.updated"
DATA_VALIDATION_FAILED = "data.validation.failed"

USER_ACTION = "user.action"
CONFIGURATION_CHANGED = "configuration.changed"
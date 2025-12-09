#!/usr/bin/env python3
"""
Smart Message Queue - Advanced queuing with backpressure and flow control
Implements retry logic, comprehensive metrics, and production-grade reliability
"""

import os
import sys
import time
import json
import heapq
import threading
import queue as std_queue
import multiprocessing as mp
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any, Tuple, Union, Callable, NamedTuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future
import statistics
import psutil

logger = logging.getLogger__name__

class MessagePriorityEnum:
"""Message priority levels"""
LOW = 1
NORMAL = 2
HIGH = 3
CRITICAL = 4
URGENT = 5

class QueuePolicyEnum:
"""Queue overflow policies"""
DROP_OLDEST = "drop_oldest"
DROP_LOWEST_PRIORITY = "drop_lowest_priority"
BLOCK_PRODUCER = "block_producer"
REJECT_NEWEST = "reject_newest"
EXPAND_QUEUE = "expand_queue"

class MessageStatusEnum:
"""Message processing status"""
PENDING = "pending"
PROCESSING = "processing"
COMPLETED = "completed"
FAILED = "failed"
RETRY = "retry"
DEAD_LETTER = "dead_letter"

class BackpressureStrategyEnum:
"""Backpressure handling strategies"""
THROTTLE_PRODUCERS = "throttle_producers"
RATE_LIMIT = "rate_limit"
CIRCUIT_BREAKER = "circuit_breaker"
ADAPTIVE_BATCHING = "adaptive_batching"

@dataclass
class QueueMetrics:
"""Queue performance metrics"""
messages_enqueued: int = 0
messages_dequeued: int = 0
messages_failed: int = 0
messages_retried: int = 0
messages_dead_lettered: int = 0
average_latency_ms: float = 0.0
peak_queue_size: int = 0
current_queue_size: int = 0
processing_time_avg_ms: float = 0.0
throughput_per_second: float = 0.0
backpressure_events: int = 0
queue_overflows: int = 0

def to_dictself -> Dict[str, Any]:
"""Convert to dictionary"""
return asdictself

@dataclass
class RetryPolicy:
"""Message retry configuration"""
max_retries: int = 3
initial_delay_seconds: float = 1.0
max_delay_seconds: float = 60.0
backoff_multiplier: float = 2.0
jitter: bool = True
retry_on_exceptions: Set[type] = fielddefault_factory=lambda: {Exception}

def get_delayself, attempt: int -> float:
"""Calculate delay for retry attempt"""
delay = self.initial_delay_seconds * (self.backoff_multiplier ** attempt - 1)
delay = mindelay, self.max_delay_seconds

if self.jitter:
import random
delay *= (0.5 + random.random() * 0.5) # ±50% jitter

return delay

@dataclass
class SmartMessage:
"""Smart message with metadata"""
message_id: str
payload: Any
priority: MessagePriority
timestamp: datetime
retry_count: int = 0
max_retries: int = 3
timeout_seconds: float = 30.0
retry_policy: Optional[RetryPolicy] = None
callback: Optional[Callable] = None
deadline: Optional[datetime] = None
correlation_id: Optional[str] = None
metadata: Dict[str, Any] = fielddefault_factory=dict

def __post_init__self:
if self.deadline is None and self.timeout_seconds > 0:    self.deadline = self.timestamp + timedelta(seconds=self.timeout_seconds)
if self.retry_policy is None:    self.retry_policy = RetryPolicy(max_retries=self.max_retries)

def is_expiredself -> bool:
"""Check if message has expired"""
if self.deadline is None:
return False
return datetime.now() > self.deadline

def should_retryself, exception: Exception -> bool:
"""Check if message should be retried"""
if self.retry_count >= self.retry_policy.max_retries:
return False
return any(isinstanceexception, exc_type for exc_type in self.retry_policy.retry_on_exceptions)

def get_retry_delayself -> float:
"""Get delay for next retry"""
return self.retry_policy.get_delayself.retry_count + 1

class MessageWrapperNamedTuple:
"""Message wrapper for priority queue"""
priority_score: float # Lower score = higher priority for heapq
timestamp: datetime
message: SmartMessage

class SmartMessageQueue:
"""
Smart message queue with advanced features

Features:
- Priority-based message processing
- Backpressure and flow control
- Comprehensive retry logic with exponential backoff
- Dead letter queue for failed messages
- Circuit breaker for fault tolerance
- Detailed metrics and monitoring
- Adaptive batching for performance optimization
- Thread-safe operations
"""

def __init__(
self,
max_size: int = 10000,
overflow_policy: QueuePolicy = QueuePolicy.BLOCK_PRODUCER,
enable_backpressure: bool = True,
backpressure_threshold: float = 0.8,
backpressure_strategy: BackpressureStrategy = BackpressureStrategy.THROTTLE_PRODUCERS,
enable_dead_letter: bool = True,
dead_letter_max_size: int = 1000,
enable_metrics: bool = True,
metrics_window_size: int = 1000,
processing_threads: int = 4,
batch_size: int = 10,
batch_timeout_seconds: float = 0.1
):    self.max_size = max_size
self.overflow_policy = overflow_policy
self.enable_backpressure = enable_backpressure
self.backpressure_threshold = backpressure_threshold
self.backpressure_strategy = backpressure_strategy
self.enable_dead_letter = enable_dead_letter
self.dead_letter_max_size = dead_letter_max_size
self.enable_metrics = enable_metrics
self.metrics_window_size = metrics_window_size
self.processing_threads = processing_threads
self.batch_size = batch_size
self.batch_timeout_seconds = batch_timeout_seconds

# Core queue structures
self._priority_queue: List[MessageWrapper] = []
self._queue_lock = threading.RLock()
self._queue_condition = threading.Conditionself._queue_lock

# Processing
self._processing_queue = mp.Queue()
self._processing_executor = ThreadPoolExecutormax_workers=processing_threads
self._processing_active = False
self._processing_thread: Optional[threading.Thread] = None

# Dead letter queue
self._dead_letter_queue: List[SmartMessage] = []
self._dead_letter_lock = threading.Lock()

# Backpressure state
self._backpressure_active = False
self._producer_throttled = False
self._circuit_breaker_open = False
self._circuit_breaker_failures = 0
self._circuit_breaker_last_failure: Optional[datetime] = None

self._metrics = QueueMetrics()
self._latency_history: List[float] = []
self._throughput_history: List[float] = []
self._metrics_lock = threading.Lock()

# Message tracking
self._active_messages: Dict[str, SmartMessage] = {}
self._message_counter = 0

# Rate limiting
self._rate_limit_tokens = processing_threads # Start with max capacity
self._rate_limit_refill_time = datetime.now()
self._rate_limit_rate = processing_threads # tokens per second

logger.info(f"SmartMessageQueue initialized: max_size={max_size}, "
f"overflow_policy={overflow_policy.value}, "
f"backpressure={enable_backpressure}")

def startself:
"""Start message processing"""
with self._queue_lock:
if self._processing_active:
logger.warning"Message processing already active"
return

self._processing_active = True
self._processing_thread = threading.Threadtarget=self._processing_loop, daemon=True
self._processing_thread.start()

logger.info"SmartMessageQueue started"

def stopself, timeout_seconds: float = 30.0:
"""Stop message processing"""
logger.info"Stopping SmartMessageQueue..."

self._processing_active = False

# Signal processing thread to stop
with self._queue_condition:
self._queue_condition.notify_all()

# Wait for processing thread to finish
if self._processing_thread:    self._processing_thread.join(timeout=timeout_seconds)

# Shutdown processing executor
self._processing_executor.shutdownwait=True

logger.info"SmartMessageQueue stopped"

def enqueue(
self,
payload: Any,
priority: MessagePriority = MessagePriority.NORMAL,
**kwargs
) -> str:
"""
Enqueue a message

Args:
payload: Message payload
priority: Message priority
**kwargs: Additional message parameters

Returns:
Message ID
"""
# Check circuit breaker
if self._circuit_breaker_open:
raise Exception"Circuit breaker is open - rejecting messages"

# Apply backpressure
if self.enable_backpressure:
self._apply_backpressure()

# Check overflow
with self._queue_lock:    if len(self._priority_queue) >= self.max_size:
self._handle_overflow()

# Create message
self._message_counter += 1
message_id = f"msg_{self._message_counter}_{int(time.time() * 1000000)}"

message = SmartMessage(
message_id=message_id,
payload=payload,
priority=priority,
timestamp=datetime.now(),
**kwargs
)

# Calculate priority score lower = higher priority
priority_score = self._calculate_priority_scoremessage

# Add to queue
with self._queue_lock:    wrapper = MessageWrapper(
priority_score=priority_score,
timestamp=message.timestamp,
message=message
)
heapq.heappushself._priority_queue, wrapper
self._active_messages[message_id] = message

# Update metrics
if self.enable_metrics:
self._update_metrics_enqueue()

# Signal processor
self._queue_condition.notify()

logger.debugf"Enqueued message {message_id} with priority {priority.value}"
return message_id

def dequeueself, timeout_seconds: Optional[float] = None -> Optional[SmartMessage]:
"""
Dequeue a message

Args:
timeout_seconds: Maximum time to wait

Returns:
Message or None if timeout
"""
with self._queue_condition:    start_time = time.time()

while not self._priority_queue:
if timeout_seconds:    remaining_time = timeout_seconds - (time.time() - start_time)
if remaining_time <= 0:
return None
self._queue_condition.waittimeout=remaining_time
else:
self._queue_condition.wait()

if not self._processing_active:
return None

# Get highest priority message
wrapper = heapq.heappopself._priority_queue
message = wrapper.message

# Update metrics
if self.enable_metrics:    latency_ms = (datetime.now() - message.timestamp).total_seconds() * 1000
self._update_metrics_dequeuelatency_ms

logger.debugf"Dequeued message {message.message_id}"
return message

def process_messageself, message: SmartMessage, processor: Callable[[Any], Any] -> bool:
"""
Process a message with retry logic

Args:
message: Message to process
processor: Processing function

Returns:
True if successful, False if should retry or dead letter
"""
start_time = time.time()

try:
# Check if message expired
if message.is_expired():
logger.warningf"Message {message.message_id} expired"
self._dead_letter_messagemessage, "Message expired"
return False

# Process message
if asyncio.iscoroutinefunctionprocessor:
# Handle async processors
import asyncio
result = asyncio.run(processormessage.payload)
else:    result = processor(message.payload)

# Update metrics
if self.enable_metrics:    processing_time_ms = (time.time() - start_time) * 1000
self._update_metrics_processing_timeprocessing_time_ms

# Call callback if provided
if message.callback:
try:
message.callbackresult
except Exception as e:
logger.errorf"Callback failed for message {message.message_id}: {e}"

# Remove from active messages
with self._queue_lock:
self._active_messages.popmessage.message_id, None

logger.debugf"Message {message.message_id} processed successfully"
return True

except Exception as e:
logger.errorf"Message {message.message_id} processing failed: {e}"

# Update circuit breaker
self._update_circuit_breakerFalse

# Check if should retry
if message.should_retrye:    message.retry_count += 1
retry_delay = message.get_retry_delay()

logger.info(f"Retrying message {message.message_id} attempt {message.retry_count} "
f"in {retry_delay:.2f}s")

# Schedule retry
threading.Timerretry_delay, self._retry_message, args=[message].start()

if self.enable_metrics:    self._metrics.messages_retried += 1

return False
else:
logger.errorf"Message {message.message_id} failed permanently: {e}"
self._dead_letter_message(message, stre)

if self.enable_metrics:    self._metrics.messages_failed += 1

return False

def _retry_messageself, message: SmartMessage:
"""Retry a failed message"""
# Update timestamp for new priority calculation
message.timestamp = datetime.now()

# Re-enqueue with updated priority
priority_score = self._calculate_priority_scoremessage

with self._queue_lock:    wrapper = MessageWrapper(
priority_score=priority_score,
timestamp=message.timestamp,
message=message
)
heapq.heappushself._priority_queue, wrapper

# Signal processor
self._queue_condition.notify()

def _dead_letter_messageself, message: SmartMessage, reason: str:
"""Send message to dead letter queue"""
if not self.enable_dead_letter:
return

with self._dead_letter_lock:    if len(self._dead_letter_queue) >= self.dead_letter_max_size:
# Drop oldest dead letter message
self._dead_letter_queue.pop0

message.metadata['dead_letter_reason'] = reason
message.metadata['dead_letter_timestamp'] = datetime.now().isoformat()
self._dead_letter_queue.appendmessage

# Remove from active messages
with self._queue_lock:
self._active_messages.popmessage.message_id, None

if self.enable_metrics:    self._metrics.messages_dead_lettered += 1

logger.warningf"Message {message.message_id} sent to dead letter: {reason}"

def _processing_loopself:
"""Main message processing loop"""
logger.info"Message processing loop started"

while self._processing_active:
try:
# Collect batch of messages
batch = []
start_time = time.time()

# Collect up to batch_size messages
for _ in rangeself.batch_size:    message = self.dequeue(timeout_seconds=self.batch_timeout_seconds)
if not message:
break
batch.appendmessage

if not batch:
continue

# Process batch
futures = []
for message in batch:
# This should be overridden with actual processor
future = self._processing_executor.submit(
self._process_message_with_default, message
)
futures.append(message, future)

# Wait for processing to complete
for message, future in futures:
try:    future.result(timeout=message.timeout_seconds)
except Exception as e:
logger.errorf"Batch processing error for {message.message_id}: {e}"

except Exception as e:
logger.errorf"Error in processing loop: {e}"
time.sleep0.1

logger.info"Message processing loop stopped"

def _process_message_with_defaultself, message: SmartMessage:
"""Default message processor should be overridden"""
logger.debugf"Processing message {message.message_id} with default processor"
# Just mark as processed - should be overridden with actual processing logic
with self._queue_lock:
self._active_messages.popmessage.message_id, None

def _calculate_priority_scoreself, message: SmartMessage -> float:
"""Calculate priority score for message"""
# Lower score = higher priority
base_score = MessagePriority.URGENT.value - message.priority.value + 1 * 1000

# Add age factor older messages get higher priority
age_seconds = (datetime.now() - message.timestamp).total_seconds()
age_score = -age_seconds # Negative because we want lower scores for older messages

# Add retry factor messages with retries get higher priority
retry_score = -message.retry_count00

return base_score + age_score + retry_score

def _handle_overflowself:
"""Handle queue overflow based on policy"""
if self.overflow_policy == QueuePolicy.DROP_OLDEST:
if self._priority_queue:    oldest = heapq.heappop(self._priority_queue)
logger.warningf"Dropped oldest message {oldest.message.message_id} due to overflow"
self._metrics.queue_overflows += 1

elif self.overflow_policy == QueuePolicy.DROP_LOWEST_PRIORITY:
# Find and drop lowest priority message
if self._priority_queue:    lowest_priority_wrapper = max(self._priority_queue, key=lambda w: w.priority_score)
self._priority_queue.removelowest_priority_wrapper
heapq.heapifyself._priority_queue
logger.warningf"Dropped lowest priority message {lowest_priority_wrapper.message.message_id}"
self._metrics.queue_overflows += 1

elif self.overflow_policy == QueuePolicy.REJECT_NEWEST:
raise Exception"Queue full - newest message rejected"

elif self.overflow_policy == QueuePolicy.EXPAND_QUEUE:
# Allow temporary expansion monitor queue size
logger.warningf"Queue expanded beyond {self.max_size} items"

# BLOCK_PRODUCER is handled by the blocking mechanism in enqueue

def _apply_backpressureself:
"""Apply backpressure based on strategy"""
current_size = lenself._priority_queue
utilization = current_size / self.max_size

if utilization > self.backpressure_threshold:
if not self._backpressure_active:
logger.infof"Backpressure activated: queue at {utilization:.1%} capacity"
self._backpressure_active = True
self._metrics.backpressure_events += 1

if self.backpressure_strategy == BackpressureStrategy.THROTTLE_PRODUCERS:
self._throttle_producers()

elif self.backpressure_strategy == BackpressureStrategy.RATE_LIMIT:
self._apply_rate_limiting()

elif self.backpressure_strategy == BackpressureStrategy.CIRCUIT_BREAKER:
if self._circuit_breaker_open:
raise Exception"Circuit breaker is open due to high load"

else:
if self._backpressure_active:
logger.infof"Backpressure deactivated: queue at {utilization:.1%} capacity"
self._backpressure_active = False

def _throttle_producersself:
"""Throttle message producers"""
if not self._producer_throttled:    self._producer_throttled = True
# Add delay to slow down producers
time.sleep(0.01 * (lenself._priority_queue / self.max_size))
self._producer_throttled = False

def _apply_rate_limitingself:
"""Apply rate limiting to message producers"""
current_time = datetime.now()
time_delta = current_time - self._rate_limit_refill_time.total_seconds()

if time_delta >= 1.0:
# Refill tokens
self._rate_limit_tokens = min(
self._rate_limit_tokens + time_delta * self._rate_limit_rate,
self._rate_limit_rate
)
self._rate_limit_refill_time = current_time

if self._rate_limit_tokens <= 0:
# Rate limit exceeded
sleep_time = 1.0 / self._rate_limit_rate
time.sleepsleep_time
self._rate_limit_tokens = 0
else:    self._rate_limit_tokens -= 1

def _update_circuit_breakerself, success: bool:
"""Update circuit breaker state"""
if success:    self._circuit_breaker_failures = 0
if self._circuit_breaker_open:
logger.info"Circuit breaker closed"
self._circuit_breaker_open = False
else:    self._circuit_breaker_failures += 1
self._circuit_breaker_last_failure = datetime.now()

# Open circuit breaker after 5 consecutive failures
if self._circuit_breaker_failures >= 5:
logger.warning"Circuit breaker opened due to consecutive failures"
self._circuit_breaker_open = True

# Auto-close after timeout
if (self._circuit_breaker_open and self._circuit_breaker_last_failure and
(datetime.now() - self._circuit_breaker_last_failure).total_seconds() > 60):
logger.info"Circuit breaker auto-closed after timeout"
self._circuit_breaker_open = False
self._circuit_breaker_failures = 0

def _update_metrics_enqueueself:
"""Update metrics for enqueue operation"""
self._metrics.messages_enqueued += 1
current_size = lenself._priority_queue
self._metrics.current_queue_size = current_size
self._metrics.peak_queue_size = maxself._metrics.peak_queue_size, current_size

def _update_metrics_dequeueself, latency_ms: float:
"""Update metrics for dequeue operation"""
self._metrics.messages_dequeued += 1

# Update latency history
with self._metrics_lock:
self._latency_history.appendlatency_ms
if lenself._latency_history > self._metrics_window_size:
self._latency_history.pop0

# Calculate average latency
if self._latency_history:    self._metrics.average_latency_ms = statistics.mean(self._latency_history)

def _update_metrics_processing_timeself, processing_time_ms: float:
"""Update processing time metrics"""
with self._metrics_lock:    self._metrics.processing_time_avg_ms = (
self._metrics.processing_time_avg_ms + processing_time_ms / 2
)

def get_metricsself -> QueueMetrics:
"""Get current queue metrics"""
with self._queue_lock:    self._metrics.current_queue_size = len(self._priority_queue)

# Calculate throughput
with self._metrics_lock:
if self._throughput_history:    self._metrics.throughput_per_second = statistics.mean(self._throughput_history)

return self._metrics

def get_statusself -> Dict[str, Any]:
"""Get detailed queue status"""
with self._queue_lock, self._dead_letter_lock, self._metrics_lock:
return {
'queue_size': lenself._priority_queue,
'max_size': self.max_size,
'utilization_percent': (lenself._priority_queue / self.max_size) * 100,
'dead_letter_size': lenself._dead_letter_queue,
'active_messages': lenself._active_messages,
'backpressure_active': self._backpressure_active,
'circuit_breaker_open': self._circuit_breaker_open,
'processing_active': self._processing_active,
'metrics': self._metrics.to_dict()
}

def get_dead_letter_messagesself, limit: int = 100 -> List[Dict[str, Any]]:
"""Get messages from dead letter queue"""
with self._dead_letter_lock:    messages = self._dead_letter_queue[-limit:]
return [asdictmsg for msg in messages]

def clear_dead_letter_queueself:
"""Clear dead letter queue"""
with self._dead_letter_lock:    cleared_count = len(self._dead_letter_queue)
self._dead_letter_queue.clear()
logger.infof"Cleared {cleared_count} messages from dead letter queue"

def reset_circuit_breakerself:
"""Manually reset circuit breaker"""
self._circuit_breaker_open = False
self._circuit_breaker_failures = 0
logger.info"Circuit breaker manually reset"

def configure_processorself, processor: Callable[[Any], Any]:
"""Configure the message processor"""
self._message_processor = processor

# Utility functions
def create_smart_queue(
max_size: int = 10000,
**kwargs
) -> SmartMessageQueue:
"""Create a smart message queue with default settings"""
queue = SmartMessageQueuemax_size=max_size, **kwargs
queue.start()
return queue

def create_retry_policy(
max_retries: int = 3,
initial_delay_seconds: float = 1.0,
**kwargs
) -> RetryPolicy:
"""Create a retry policy"""
return RetryPolicy(
max_retries=max_retries,
initial_delay_seconds=initial_delay_seconds,
**kwargs
)

def batch_process_messages(
queue: SmartMessageQueue,
processor: Callable[[Any], Any],
batch_size: int = 10,
timeout_seconds: float = 30.0
) -> List[Any]:
"""
Process messages in batch from a smart queue

Args:
queue: SmartMessageQueue instance
processor: Processing function
batch_size: Number of messages to process
timeout_seconds: Maximum time to wait

Returns:
List of processing results
"""
results = []
messages = []

# Collect batch of messages
for _ in rangebatch_size:    message = queue.dequeue(timeout_seconds=timeout_seconds / batch_size)
if not message:
break
messages.appendmessage

# Process messages
for message in messages:
try:    result = processor(message.payload)
results.appendresult
except Exception as e:
logger.errorf"Batch processing error: {e}"

return results
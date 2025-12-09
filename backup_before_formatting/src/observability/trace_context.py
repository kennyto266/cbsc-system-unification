"""
Distributed Tracing Context

Provides distributed tracing capabilities with trace IDs and span IDs
for tracking requests across service boundaries.
"""

import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SpanStatus(Enum):
    """Span execution status"""

    OK = "OK"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"


@dataclass
class TraceContext:
    """Distributed tracing context"""

    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    operation_name: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: SpanStatus = SpanStatus.OK
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    user_id: Optional[str] = None

    def finish(self, status: SpanStatus = SpanStatus.OK) -> None:
        """Mark span as finished"""
        self.end_time = time.time()
        self.status = status

    def add_tag(self, key: str, value: Any) -> None:
        """Add a tag to the span"""
        self.tags[key] = value

    def add_log(self, message: str, level: str = "info") -> None:
        """Add a log to the span"""
        self.logs.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "message": message,
                "level": level,
            }
        )

    def get_duration_ms(self) -> float:
        """Get span duration in milliseconds"""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return (time.time() - self.start_time) * 1000


class TraceManager:
    """Manager for distributed tracing"""

    def __init__(self) -> None:
        self._current_context: Optional[TraceContext] = None
        self._spans: List[TraceContext] = []
        self._lock = threading.RLock()
        self._max_spans = 10000  # Limit number of spans to prevent memory issues

    def start_span(
        self,
        operation_name: str,
        parent_span_id: Optional[str] = None,
        user_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> TraceContext:
        """Start a new span"""
        with self._lock:
            # Generate or use provided trace ID
            if trace_id is None:
                trace_id = str(uuid.uuid4()).replace("-", "")

            # Generate span ID
            span_id = str(uuid.uuid4()).replace("-", "")

            # Create trace context
            context = TraceContext(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                operation_name=operation_name,
                user_id=user_id,
            )

            # Set as current context
            self._current_context = context
            self._spans.append(context)

            # Limit number of spans
            if len(self._spans) > self._max_spans:
                self._spans = self._spans[-self._max_spans // 2 :]

            return context

    def get_current_span(self) -> Optional[TraceContext]:
        """Get the current active span"""
        with self._lock:
            return self._current_context

    def finish_span(self, status: SpanStatus = SpanStatus.OK) -> Optional[TraceContext]:
        """Finish the current span"""
        with self._lock:
            if self._current_context:
                self._current_context.finish(status)
                span = self._current_context
                self._current_context = None
                return span
            return None

    def get_all_spans(self) -> List[TraceContext]:
        """Get all recorded spans"""
        with self._lock:
            return self._spans.copy()

    def get_spans_by_trace_id(self, trace_id: str) -> List[TraceContext]:
        """Get all spans for a specific trace"""
        with self._lock:
            return [span for span in self._spans if span.trace_id == trace_id]

    def get_trace_summary(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of a trace"""
        with self._lock:
            spans = self.get_spans_by_trace_id(trace_id)

            if not spans:
                return None

            # Calculate trace statistics
            root_span = next((s for s in spans if s.parent_span_id is None), None)
            all_durations = [s.get_duration_ms() for s in spans if s.end_time]
            total_duration = max(all_durations) if all_durations else 0

            return {
                "trace_id": trace_id,
                "span_count": len(spans),
                "root_span": root_span.operation_name if root_span else "unknown",
                "total_duration_ms": total_duration,
                "status_counts": {
                    status.value: sum(1 for s in spans if s.status == status)
                    for status in SpanStatus
                },
                "user_id": root_span.user_id if root_span else None,
                "start_time": min(s.start_time for s in spans),
                "end_time": max(s.end_time for s in spans if s.end_time),
                "spans": [
                    {
                        "span_id": s.span_id,
                        "operation_name": s.operation_name,
                        "duration_ms": s.get_duration_ms(),
                        "status": s.status.value,
                        "tags": s.tags,
                    }
                    for s in sorted(spans, key=lambda x: x.start_time)
                ],
            }

    def export_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Export a trace in a standard format"""
        with self._lock:
            return self.get_trace_summary(trace_id)

    def clear_finished_spans(self) -> int:
        """Clear all finished spans and return count"""
        with self._lock:
            before_count = len(self._spans)
            self._spans = [s for s in self._spans if s.end_time is None]
            return before_count - len(self._spans)

    def get_active_spans_count(self) -> int:
        """Get count of active (unfinished) spans"""
        with self._lock:
            return sum(1 for s in self._spans if s.end_time is None)


# Global trace manager instance
_trace_manager = TraceManager()


def get_trace_manager() -> TraceManager:
    """Get the global trace manager instance"""
    return _trace_manager


# Context manager for spans
class trace_span:
    """Context manager for creating spans"""

    def __init__(
        self,
        operation_name: str,
        user_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ):
        self.operation_name = operation_name
        self.user_id = user_id
        self.trace_id = trace_id
        self.span: Optional[TraceContext] = None
        self.manager = get_trace_manager()

    def __enter__(self) -> Optional[TraceContext]:
        self.span = self.manager.start_span(
            operation_name=self.operation_name,
            user_id=self.user_id,
            trace_id=self.trace_id,
        )
        return self.span

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.span:
            if exc_type is not None:
                self.span.finish(SpanStatus.ERROR)
                if self.span.logs:
                    self.span.add_log(f"Exception: {exc_val}", "error")
            else:
                self.span.finish(SpanStatus.OK)


# Utility functions
def generate_trace_id() -> str:
    """Generate a new trace ID"""
    return str(uuid.uuid4()).replace("-", "")


def generate_span_id() -> str:
    """Generate a new span ID"""
    return str(uuid.uuid4()).replace("-", "")


def get_current_trace_id() -> Optional[str]:
    """Get current trace ID from context"""
    current_span = get_trace_manager().get_current_span()
    return current_span.trace_id if current_span else None

"""
Performance Metrics Middleware for FastAPI

This module provides comprehensive performance monitoring and metrics collection
for all API requests, including execution time, memory usage, CPU utilization,
and bottleneck detection.
"""

import asyncio
import json
import logging
import threading
import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

import psutil
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.observability.metrics_registry import MetricNames, get_metrics_registry
from src.observability.structured_logger import get_observability_logger
from src.observability.trace_context import (
    get_trace_manager,
)

logger = logging.getLogger(__name__)


class PerformanceMetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect and attach performance metrics to all responses

    This middleware automatically:
    - Collects execution time and CPU time
    - Monitors memory usage before and after request
    - Tracks system resource utilization
    - Generates trace IDs for distributed tracing
    - Attaches metrics to response headers and body
    - Records metrics to the observability system
    """

    def __init__(self, app, collect_detailed: bool = True):
        super().__init__(app)
        self.collect_detailed = collect_detailed
        self.logger = get_observability_logger("api_performance")
        self.metrics = get_metrics_registry()
        self.trace_manager = get_trace_manager()
        self._lock = threading.Lock()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect performance metrics"""
        # Start timing
        start_time = time.time()
        start_cpu = time.process_time()

        # Get system state before request
        system_state_before = self._get_system_state()

        # Create trace context for distributed tracing
        trace_context = self.trace_manager.start_span(
            operation_name=f"{request.method} {request.url.path}",
            user_id=self._get_user_id(request),
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Record error
            self.logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            trace_context.finish()
            raise

        # Calculate metrics
        end_time = time.time()
        end_cpu = time.process_time()

        execution_time_ms = int((end_time - start_time) * 1000)
        cpu_time_ms = int((end_cpu - start_cpu) * 1000)
        system_state_after = self._get_system_state()

        # Get response data for attaching metrics
        response_dict = None
        if hasattr(response, "body"):
            try:
                response_body = (
                    response.body.decode("utf - 8")
                    if isinstance(response.body, bytes)
                    else response.body
                )
                response_dict = json.loads(response_body) if response_body else None
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        # Create comprehensive performance metrics
        performance_metrics = {
            "timing": {
                "total_time_ms": execution_time_ms,
                "cpu_time_ms": cpu_time_ms,
                "wall_time_ms": execution_time_ms,
            },
            "resource_usage": {
                "memory_delta_mb": system_state_after["memory_mb"]
                - system_state_before["memory_mb"],
                "memory_peak_mb": system_state_after["memory_mb"],
                "memory_available_mb": system_state_after["available_mb"],
                "cpu_utilization": system_state_after["cpu_percent"],
            },
            "request_info": {
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params)[
                    :100
                ],  # Truncate long query strings
                "status_code": response.status_code,
            },
            "observability": {
                "trace_id": trace_context.trace_id,
                "span_id": trace_context.span_id,
                "correlation_id": f"req-{int(time.time() * 1000)}-{trace_context.span_id[:8]}",
            },
        }

        # Record metrics to observability system
        self._record_metrics(request, performance_metrics)

        # Add performance headers to response
        response.headers["X - Performance - Time - MS"] = str(execution_time_ms)
        response.headers["X - Performance - Memory - MB"] = (
            f"{performance_metrics['resource_usage']['memory_peak_mb']:.2f}"
        )
        response.headers["X - Trace - ID"] = performance_metrics["observability"][
            "trace_id"
        ]
        response.headers["X - CPU - Time - MS"] = str(cpu_time_ms)

        # Attach metrics to response body for JSON responses
        if response_dict and isinstance(response_dict, dict):
            response_dict["_performance"] = performance_metrics
            response = JSONResponse(
                content=response_dict,
                status_code=response.status_code,
                headers=response.headers,
            )

        # Log performance with structured data
        self.logger.info(
            f"Request completed: {request.method} {request.url.path}",
            extra={
                "correlation_id": performance_metrics["observability"][
                    "correlation_id"
                ],
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "execution_time_ms": execution_time_ms,
                "cpu_time_ms": cpu_time_ms,
                "memory_mb": performance_metrics["resource_usage"]["memory_peak_mb"],
                "user_action": "api_request_completed",
            },
        )

        # Finish trace
        trace_context.finish()

        return response

    def _get_system_state(self) -> Dict[str, Any]:
        """Get current system state including memory and CPU usage"""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(
                interval=0.01
            )  # Short interval for performance

            return {
                "memory_mb": memory.used / (1024 * 1024),
                "available_mb": memory.available / (1024 * 1024),
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
            }
        except Exception as e:
            # Fallback if psutil fails
            logger.warning(f"Failed to get system state: {e}")
            return {
                "memory_mb": 0,
                "available_mb": 0,
                "cpu_percent": 0,
                "memory_percent": 0,
            }

    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request headers"""
        # In production, extract from auth token or session
        return (
            request.headers.get("X - User - ID")
            or request.headers.get("Authorization", "anonymous")[:50]
        )

    def _record_metrics(self, request: Request, metrics: Dict[str, Any]):
        """Record metrics to the observability system"""
        # Record request duration histogram
        self.metrics.record_histogram(
            MetricNames.API_REQUEST_DURATION_MS,
            metrics["timing"]["total_time_ms"],
            labels={
                "method": request.method,
                "path": request.url.path,
                "status_code": str(metrics["request_info"]["status_code"]),
            },
        )

        # Record memory usage histogram
        self.metrics.record_histogram(
            MetricNames.API_REQUEST_MEMORY_USAGE_MB,
            metrics["resource_usage"]["memory_peak_mb"],
            labels={"method": request.method, "path": request.url.path},
        )

        # Record request counter
        self.metrics.increment_counter(
            MetricNames.API_REQUESTS_TOTAL,
            labels={
                "method": request.method,
                "path": request.url.path,
                "status_code": str(metrics["request_info"]["status_code"]),
            },
        )

        # Record slow requests
        if metrics["timing"]["total_time_ms"] > 1000:
            self.metrics.increment_counter(
                MetricNames.API_SLOW_REQUESTS_TOTAL,
                labels={"method": request.method, "path": request.url.path},
            )

        # Record high memory requests
        if metrics["resource_usage"]["memory_peak_mb"] > 500:
            self.metrics.increment_counter(MetricNames.API_HIGH_MEMORY_REQUESTS_TOTAL)

        # Update gauges for current system state
        self.metrics.set_gauge(
            MetricNames.SYSTEM_MEMORY_USAGE_MB,
            metrics["resource_usage"]["memory_peak_mb"],
        )
        self.metrics.set_gauge(
            MetricNames.SYSTEM_CPU_USAGE_PERCENT,
            metrics["resource_usage"]["cpu_utilization"],
        )


def performance_monitor(threshold_ms: int = 1000):
    """
    Decorator to monitor function performance

    Args:
        threshold_ms: Alert threshold in milliseconds

    Usage:
        @performance_monitor(threshold_ms=500)
        async def my_function():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            logger = get_observability_logger(func.__module__)

            try:
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # Calculate performance metrics
                execution_time_ms = int((time.time() - start_time) * 1000)
                memory_usage_mb = (
                    psutil.Process().memory_info().rss / (1024 * 1024)
                ) - start_memory

                # Record metrics
                metrics = get_metrics_registry()
                metrics.record_histogram(
                    MetricNames.FUNCTION_EXECUTION_DURATION_MS,
                    execution_time_ms,
                    labels={"function": func.__name__},
                )
                metrics.record_histogram(
                    MetricNames.FUNCTION_MEMORY_DELTA_MB,
                    memory_usage_mb,
                    labels={"function": func.__name__},
                )

                # Log slow function execution
                if execution_time_ms > threshold_ms:
                    logger.warning(
                        f"Slow function execution: {func.__name__}",
                        extra={
                            "function": func.__name__,
                            "execution_time_ms": execution_time_ms,
                            "memory_delta_mb": memory_usage_mb,
                            "threshold_ms": threshold_ms,
                        },
                    )

                return result

            except Exception as e:
                execution_time_ms = int((time.time() - start_time) * 1000)
                logger.error(
                    f"Function execution failed: {func.__name__}",
                    extra={
                        "function": func.__name__,
                        "execution_time_ms": execution_time_ms,
                        "error": str(e),
                    },
                )
                raise

        return wrapper

    return decorator


class PerformanceProfiler:
    """
    Performance profiler for detecting and analyzing bottlenecks

    This profiler maintains a history of endpoint performance and provides
    methods to identify slow endpoints, high memory usage, and other issues.
    """

    def __init__(self):
        self.profiles: Dict[str, List[Dict[str, Any]]] = {}
        self.lock = threading.Lock()
        self.logger = get_observability_logger("performance_profiler")
        self.max_profiles_per_endpoint = 1000

    def profile_endpoint(
        self,
        method: str,
        path: str,
        execution_time_ms: int,
        memory_usage_mb: float,
        status_code: int,
    ):
        """Profile an API endpoint with performance data"""
        endpoint = f"{method} {path}"

        with self.lock:
            if endpoint not in self.profiles:
                self.profiles[endpoint] = []

            profile = {
                "timestamp": datetime.utcnow().isoformat(),
                "execution_time_ms": execution_time_ms,
                "memory_usage_mb": memory_usage_mb,
                "status_code": status_code,
            }

            self.profiles[endpoint].append(profile)

            # Keep only the most recent profiles to prevent memory issues
            if len(self.profiles[endpoint]) > self.max_profiles_per_endpoint:
                self.profiles[endpoint] = self.profiles[endpoint][
                    -self.max_profiles_per_endpoint // 2 :
                ]

    def get_bottlenecks(self, endpoint: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Detect performance bottlenecks

        Args:
            endpoint: Specific endpoint to check (None for all endpoints)

        Returns:
            List of detected bottlenecks sorted by severity
        """
        bottlenecks = []

        with self.lock:
            endpoints = [endpoint] if endpoint else list(self.profiles.keys())

            for ep in endpoints:
                if ep not in self.profiles:
                    continue

                profiles = self.profiles[ep]
                if len(profiles) < 10:  # Need at least 10 samples
                    continue

                # Calculate statistics for execution time
                execution_times = [p["execution_time_ms"] for p in profiles]
                avg_time = sum(execution_times) / len(execution_times)
                p95_time = sorted(execution_times)[int(len(execution_times) * 0.95)]
                p99_time = sorted(execution_times)[int(len(execution_times) * 0.99)]

                # Detect latency bottlenecks
                if p95_time > 1000:
                    bottlenecks.append(
                        {
                            "endpoint": ep,
                            "issue": "high_latency",
                            "severity": "high" if p99_time > 2000 else "medium",
                            "p95_latency_ms": p95_time,
                            "p99_latency_ms": p99_time,
                            "avg_latency_ms": avg_time,
                            "request_count": len(profiles),
                            "recommendation": "Consider optimization, caching, or async processing",
                        }
                    )

                # Check for memory issues
                memory_usage = [p["memory_usage_mb"] for p in profiles]
                avg_memory = sum(memory_usage) / len(memory_usage)
                p95_memory = sorted(memory_usage)[int(len(memory_usage) * 0.95)]
                p99_memory = sorted(memory_usage)[int(len(memory_usage) * 0.99)]

                if p95_memory > 200:
                    bottlenecks.append(
                        {
                            "endpoint": ep,
                            "issue": "high_memory_usage",
                            "severity": (
                                "high"
                                if p95_memory > 500 or p99_memory > 1000
                                else "medium"
                            ),
                            "p95_memory_mb": p95_memory,
                            "p99_memory_mb": p99_memory,
                            "avg_memory_mb": avg_memory,
                            "request_count": len(profiles),
                            "recommendation": "Consider data chunking, streaming, or memory optimization",
                        }
                    )

                # Check for high error rates
                error_count = sum(1 for p in profiles if p["status_code"] >= 400)
                error_rate = error_count / len(profiles) * 100

                if error_rate > 5:
                    bottlenecks.append(
                        {
                            "endpoint": ep,
                            "issue": "high_error_rate",
                            "severity": "high" if error_rate > 20 else "medium",
                            "error_rate_percent": error_rate,
                            "error_count": error_count,
                            "request_count": len(profiles),
                            "recommendation": "Investigate error causes, add proper error handling",
                        }
                    )

        # Sort by severity and then by impact
        return sorted(
            bottlenecks,
            key=lambda x: (x["severity"] == "high", x.get("p95_latency_ms", 0)),
            reverse=True,
        )

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary across all endpoints"""
        with self.lock:
            total_requests = sum(len(profiles) for profiles in self.profiles.values())

            if total_requests == 0:
                return {
                    "message": "No performance data available",
                    "total_requests": 0,
                    "endpoints_monitored": 0,
                }

            # Aggregate statistics
            all_times = []
            all_memory = []

            for profiles in self.profiles.values():
                all_times.extend([p["execution_time_ms"] for p in profiles])
                all_memory.extend([p["memory_usage_mb"] for p in profiles])

            # Sort for percentiles
            sorted_times = sorted(all_times)
            sorted_memory = sorted(all_memory)

            # Calculate statistics
            summary = {
                "total_requests": total_requests,
                "endpoints_monitored": len(self.profiles),
                "avg_execution_time_ms": sum(all_times) / len(all_times),
                "p50_execution_time_ms": sorted_times[int(len(sorted_times) * 0.5)],
                "p95_execution_time_ms": sorted_times[int(len(sorted_times) * 0.95)],
                "p99_execution_time_ms": sorted_times[int(len(sorted_times) * 0.99)],
                "avg_memory_usage_mb": sum(all_memory) / len(all_memory),
                "p95_memory_usage_mb": sorted_memory[int(len(sorted_memory) * 0.95)],
                "p99_memory_usage_mb": sorted_memory[int(len(sorted_memory) * 0.99)],
                "top_slow_endpoints": self._get_top_slow_endpoints(),
                "top_memory_intensive_endpoints": self._get_top_memory_intensive_endpoints(),
                "detected_bottlenecks": self.get_bottlenecks(),
            }

            return summary

    def _get_top_slow_endpoints(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top slowest endpoints by average latency"""
        with self.lock:
            results = []

            for endpoint, profiles in self.profiles.items():
                if len(profiles) < 5:
                    continue

                times = [p["execution_time_ms"] for p in profiles]
                avg_time = sum(times) / len(times)
                p95_time = sorted(times)[int(len(times) * 0.95)]

                results.append(
                    {
                        "endpoint": endpoint,
                        "avg_latency_ms": avg_time,
                        "p95_latency_ms": p95_time,
                        "request_count": len(profiles),
                    }
                )

            return sorted(results, key=lambda x: x["p95_latency_ms"], reverse=True)[
                :limit
            ]

    def _get_top_memory_intensive_endpoints(
        self, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get top memory - intensive endpoints"""
        with self.lock:
            results = []

            for endpoint, profiles in self.profiles.items():
                if len(profiles) < 5:
                    continue

                memory_usage = [p["memory_usage_mb"] for p in profiles]
                avg_memory = sum(memory_usage) / len(memory_usage)
                p95_memory = sorted(memory_usage)[int(len(memory_usage) * 0.95)]

                results.append(
                    {
                        "endpoint": endpoint,
                        "avg_memory_mb": avg_memory,
                        "p95_memory_mb": p95_memory,
                        "request_count": len(profiles),
                    }
                )

            return sorted(results, key=lambda x: x["p95_memory_mb"], reverse=True)[
                :limit
            ]

    def clear(self) -> None:
        """Clear all performance profiles"""
        with self.lock:
            self.profiles.clear()


# Global profiler instance
_profiler = PerformanceProfiler()


def get_performance_profiler() -> PerformanceProfiler:
    """Get global performance profiler instance"""
    return _profiler


# Specialized decorators for different use cases
def monitor_backtest_performance(func: Callable) -> Callable:
    """
    Decorator to monitor backtest performance specifically

    Tracks execution time and memory usage for backtest operations
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / (1024 * 1024)

        result = (
            await func(*args, **kwargs)
            if asyncio.iscoroutinefunction(func)
            else func(*args, **kwargs)
        )

        execution_time = (time.time() - start_time) * 1000
        memory_delta = (
            psutil.Process().memory_info().rss / (1024 * 1024)
        ) - start_memory

        # Record backtest - specific metrics
        metrics = get_metrics_registry()
        metrics.record_histogram(MetricNames.BACKTEST_DURATION_MS, execution_time)
        metrics.record_histogram("backtest_memory_delta_mb", memory_delta)

        # Add performance metrics to result if it's a dict
        if isinstance(result, dict):
            if "_performance" not in result:
                result["_performance"] = {}
            result["_performance"].update(
                {
                    "backtest_execution_time_ms": int(execution_time),
                    "backtest_memory_delta_mb": memory_delta,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        return result

    return wrapper


def monitor_optimization_performance(func: Callable) -> Callable:
    """
    Decorator to monitor optimization performance

    Tracks optimization - specific performance metrics
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / (1024 * 1024)

        result = (
            await func(*args, **kwargs)
            if asyncio.iscoroutinefunction(func)
            else func(*args, **kwargs)
        )

        execution_time = (time.time() - start_time) * 1000
        memory_delta = (
            psutil.Process().memory_info().rss / (1024 * 1024)
        ) - start_memory

        # Record optimization metrics
        metrics = get_metrics_registry()
        metrics.record_histogram(
            MetricNames.BACKTEST_OPTIMIZATION_DURATION_MS, execution_time
        )
        metrics.record_histogram("optimization_memory_delta_mb", memory_delta)

        return result

    return wrapper


# API endpoints for performance monitoring
def get_performance_api_routes():
    """Get FastAPI routes for performance monitoring"""

    from fastapi import APIRouter

    router = APIRouter(prefix="/api / v1 / performance", tags=["performance"])
    profiler = get_performance_profiler()
    metrics = get_metrics_registry()
    trace_manager = get_trace_manager()

    @router.get("/summary")
    def get_performance_summary():
        """Get overall performance summary"""
        return profiler.get_performance_summary()

    @router.get("/bottlenecks")
    def get_bottlenecks():
        """Get detected performance bottlenecks"""
        bottlenecks = profiler.get_bottlenecks()
        return {"count": len(bottlenecks), "bottlenecks": bottlenecks}

    @router.get("/metrics")
    def get_metrics():
        """Get all collected metrics"""
        return metrics.get_all_metrics()

    @router.get("/traces")
    def get_traces():
        """Get all traces"""
        traces = []
        for span in trace_manager.get_all_spans():
            trace_summary = trace_manager.get_trace_summary(span.trace_id)
            if trace_summary and trace_summary not in traces:
                traces.append(trace_summary)
        return {"traces": traces}

    @router.get("/active - spans")
    def get_active_spans():
        """Get count of active (unfinished) spans"""
        return {"active_spans_count": trace_manager.get_active_spans_count()}

    @router.post("/reset")
    def reset_metrics():
        """Reset all metrics and profiles"""
        metrics.reset()
        profiler.clear()
        cleared_spans = trace_manager.clear_finished_spans()
        return {
            "status": "success",
            "message": "All metrics, profiles, and finished spans cleared",
            "cleared_spans": cleared_spans,
        }

    return router

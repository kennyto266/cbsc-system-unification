#!/usr/bin/env python3
"""
InfluxDB Monitoring and Metrics Service
InfluxDB 監控和指標服務
Phase 1.2 - 時序數據庫配置

Provides monitoring, metrics collection, and health checks for InfluxDB operations.
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import psutil
import aiohttp
from functools import wraps

from .influxdb_client import InfluxDBManager, InfluxDBConfig
from ..config.influxdb_config import get_config, BucketType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OperationMetrics:
    """Metrics for a single operation"""
    operation: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # milliseconds
    success: bool = True
    error: Optional[str] = None
    data_points: int = 0
    batch_size: Optional[int] = None
    bucket: Optional[str] = None


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    component: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    timestamp: datetime
    metrics: Dict[str, Any] = field(default_factory=dict)


class InfluxDBMonitor:
    """
    Monitors InfluxDB operations and provides health checks.
    監控 InfluxDB 操作並提供健康檢查。
    """

    def __init__(self, influxdb_manager: InfluxDBManager):
        self.manager = influxdb_manager
        self.config = get_config()

        # Metrics storage
        self.operation_metrics: deque = deque(maxlen=1000)  # Keep last 1000 operations
        self.operation_counts = defaultdict(int)
        self.operation_errors = defaultdict(int)
        self.operation_durations = defaultdict(lambda: deque(maxlen=100))
        self.bucket_sizes = defaultdict(int)

        # Performance counters
        self.total_writes = 0
        self.total_reads = 0
        self.total_errors = 0
        self.last_operation_time = None

        # Health check status
        self.health_status = {
            "influxdb": HealthCheckResult(
                component="influxdb",
                status="unknown",
                message="Not checked",
                timestamp=datetime.utcnow()
            ),
            "redis": HealthCheckResult(
                component="redis",
                status="unknown",
                message="Not checked",
                timestamp=datetime.utcnow()
            ),
            "system": HealthCheckResult(
                component="system",
                status="unknown",
                message="Not checked",
                timestamp=datetime.utcnow()
            )
        }

        # Monitoring task
        self._monitoring_task: Optional[asyncio.Task] = None
        self._monitoring_interval = 60  # seconds

        logger.info("InfluxDB monitor initialized")

    def track_operation(self, operation: str) -> Callable:
        """
        Decorator to track operations and collect metrics.
        跟蹤操作並收集指標的裝飾器。
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Start timing
                start_time = datetime.utcnow()
                metrics = OperationMetrics(
                    operation=operation,
                    start_time=start_time
                )

                # Extract bucket if available
                if 'bucket' in kwargs:
                    metrics.bucket = kwargs['bucket']

                try:
                    # Execute the function
                    result = await func(*args, **kwargs)

                    # Record successful operation
                    metrics.success = True
                    metrics.end_time = datetime.utcnow()
                    metrics.duration = (metrics.end_time - metrics.start_time).total_seconds() * 1000

                    # Update counters
                    self.operation_counts[operation] += 1
                    self.operation_durations[operation].append(metrics.duration)

                    # Track writes and reads
                    if 'write' in operation.lower():
                        self.total_writes += 1
                    elif 'query' in operation.lower() or 'read' in operation.lower():
                        self.total_reads += 1

                    # Store metrics
                    self.operation_metrics.append(metrics)
                    self.last_operation_time = metrics.end_time

                    logger.debug(f"Operation {operation} completed in {metrics.duration:.2f}ms")
                    return result

                except Exception as e:
                    # Record failed operation
                    metrics.success = False
                    metrics.error = str(e)
                    metrics.end_time = datetime.utcnow()
                    metrics.duration = (metrics.end_time - metrics.start_time).total_seconds() * 1000

                    # Update error counters
                    self.operation_counts[operation] += 1
                    self.operation_errors[operation] += 1
                    self.total_errors += 1

                    # Store metrics
                    self.operation_metrics.append(metrics)
                    self.last_operation_time = metrics.end_time

                    logger.error(f"Operation {operation} failed after {metrics.duration:.2f}ms: {e}")
                    raise

            return wrapper
        return decorator

    async def write_metrics_to_influxdb(self):
        """
        Write monitoring metrics to InfluxDB.
        將監控指標寫入 InfluxDB。
        """
        try:
            timestamp = datetime.utcnow()

            # Operation count metrics
            operation_data = []
            for operation, count in self.operation_counts.items():
                error_count = self.operation_errors[operation]
                success_rate = (count - error_count) / count if count > 0 else 0

                # Calculate average duration
                durations = self.operation_durations[operation]
                avg_duration = sum(durations) / len(durations) if durations else 0

                operation_data.append({
                    "measurement": "operation_metrics",
                    "timestamp": timestamp,
                    "tags": {
                        "operation": operation,
                        "component": "influxdb_client"
                    },
                    "fields": {
                        "count": count,
                        "error_count": error_count,
                        "success_rate": success_rate,
                        "avg_duration_ms": avg_duration,
                        "total_writes": self.total_writes,
                        "total_reads": self.total_reads,
                        "total_errors": self.total_errors
                    }
                })

            # System metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            system_data = [{
                "measurement": "system_metrics",
                "timestamp": timestamp,
                "tags": {
                    "component": "influxdb_monitor",
                    "host": "main"
                },
                "fields": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_gb": memory.used / (1024**3),
                    "memory_total_gb": memory.total / (1024**3),
                    "disk_percent": disk.percent,
                    "disk_used_gb": disk.used / (1024**3),
                    "disk_total_gb": disk.total / (1024**3),
                    "operations_per_second": len(self.operation_metrics) / 60 if self.operation_metrics else 0
                }
            }]

            # Health status metrics
            health_data = []
            for component, health in self.health_status.items():
                status_value = 1 if health.status == "healthy" else (0.5 if health.status == "degraded" else 0)
                health_data.append({
                    "measurement": "health_metrics",
                    "timestamp": timestamp,
                    "tags": {
                        "component": component,
                        "status": health.status
                    },
                    "fields": {
                        "healthy": status_value,
                        "status_code": 1 if health.status == "healthy" else (2 if health.status == "degraded" else 3)
                    }
                })

            # Write all metrics
            await self.manager.write_market_data(operation_data, "operation_metrics", BucketType.SYSTEM_METRICS.value)
            await self.manager.write_market_data(system_data, "system_metrics", BucketType.SYSTEM_METRICS.value)
            await self.manager.write_market_data(health_data, "health_metrics", BucketType.SYSTEM_METRICS.value)

            logger.debug("Monitoring metrics written to InfluxDB")

        except Exception as e:
            logger.error(f"Failed to write monitoring metrics: {e}")

    async def check_influxdb_health(self) -> HealthCheckResult:
        """
        Check InfluxDB health status.
        檢查 InfluxDB 健康狀態。
        """
        try:
            start_time = time.time()

            # Check basic connectivity
            health = self.manager._client.health()

            check_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            if health.status == "pass":
                # Check bucket availability
                buckets = self.manager._bucket_api.find_buckets()
                bucket_count = len(buckets)

                # Check recent operations
                recent_operations = [
                    m for m in self.operation_metrics
                    if (datetime.utcnow() - m.end_time).total_seconds() < 300  # Last 5 minutes
                ]

                error_rate = 0
                if recent_operations:
                    errors = sum(1 for m in recent_operations if not m.success)
                    error_rate = errors / len(recent_operations)

                # Determine status
                status = "healthy"
                message = "All systems operational"

                if check_time > 1000:  # High response time
                    status = "degraded"
                    message = f"High response time: {check_time:.2f}ms"
                elif error_rate > 0.1:  # High error rate (>10%)
                    status = "degraded"
                    message = f"High error rate: {error_rate:.2%}"

                metrics = {
                    "response_time_ms": check_time,
                    "bucket_count": bucket_count,
                    "recent_operations": len(recent_operations),
                    "error_rate": error_rate,
                    "uptime": health.message
                }

                return HealthCheckResult(
                    component="influxdb",
                    status=status,
                    message=message,
                    timestamp=datetime.utcnow(),
                    metrics=metrics
                )
            else:
                return HealthCheckResult(
                    component="influxdb",
                    status="unhealthy",
                    message=f"InfluxDB health check failed: {health.message}",
                    timestamp=datetime.utcnow()
                )

        except Exception as e:
            return HealthCheckResult(
                component="influxdb",
                status="unhealthy",
                message=f"InfluxDB health check error: {str(e)}",
                timestamp=datetime.utcnow()
            )

    async def check_redis_health(self) -> HealthCheckResult:
        """
        Check Redis health status (if configured).
        檢查 Redis 健康狀態（如果已配置）。
        """
        if not self.manager.redis_client:
            return HealthCheckResult(
                component="redis",
                status="healthy",
                message="Redis not configured",
                timestamp=datetime.utcnow()
            )

        try:
            start_time = time.time()

            # Test Redis connection
            self.manager.redis_client.ping()
            check_time = (time.time() - start_time) * 1000

            # Get Redis info
            info = self.manager.redis_client.info()
            memory_used = info.get('used_memory_human', 'N/A')
            connected_clients = info.get('connected_clients', 0)

            status = "healthy"
            message = "Redis operational"

            if check_time > 100:
                status = "degraded"
                message = f"High response time: {check_time:.2f}ms"

            metrics = {
                "response_time_ms": check_time,
                "memory_used": memory_used,
                "connected_clients": connected_clients
            }

            return HealthCheckResult(
                component="redis",
                status=status,
                message=message,
                timestamp=datetime.utcnow(),
                metrics=metrics
            )

        except Exception as e:
            return HealthCheckResult(
                component="redis",
                status="unhealthy",
                message=f"Redis health check error: {str(e)}",
                timestamp=datetime.utcnow()
            )

    async def check_system_health(self) -> HealthCheckResult:
        """
        Check system resource health.
        檢查系統資源健康狀態。
        """
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Check thresholds
            cpu_status = "healthy" if cpu_percent < 80 else ("degraded" if cpu_percent < 95 else "unhealthy")
            memory_status = "healthy" if memory.percent < 80 else ("degraded" if memory.percent < 95 else "unhealthy")
            disk_status = "healthy" if disk.percent < 80 else ("degraded" if disk.percent < 95 else "unhealthy")

            # Determine overall status
            all_statuses = [cpu_status, memory_status, disk_status]
            if "unhealthy" in all_statuses:
                status = "unhealthy"
            elif "degraded" in all_statuses:
                status = "degraded"
            else:
                status = "healthy"

            issues = []
            if cpu_status != "healthy":
                issues.append(f"CPU usage: {cpu_percent}%")
            if memory_status != "healthy":
                issues.append(f"Memory usage: {memory.percent}%")
            if disk_status != "healthy":
                issues.append(f"Disk usage: {disk.percent}%")

            message = "System resources healthy" if not issues else f"Resource pressure: {', '.join(issues)}"

            metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_free_gb": disk.free / (1024**3)
            }

            return HealthCheckResult(
                component="system",
                status=status,
                message=message,
                timestamp=datetime.utcnow(),
                metrics=metrics
            )

        except Exception as e:
            return HealthCheckResult(
                component="system",
                status="unhealthy",
                message=f"System health check error: {str(e)}",
                timestamp=datetime.utcnow()
            )

    async def run_health_checks(self):
        """
        Run all health checks and update status.
        運行所有健康檢查並更新狀態。
        """
        self.health_status["influxdb"] = await self.check_influxdb_health()
        self.health_status["redis"] = await self.check_redis_health()
        self.health_status["system"] = await self.check_system_health()

        # Log any issues
        for component, health in self.health_status.items():
            if health.status != "healthy":
                logger.warning(f"{component} health issue: {health.message}")

    async def start_monitoring(self):
        """
        Start the monitoring loop.
        啟動監控循環。
        """
        if self._monitoring_task and not self._monitoring_task.done():
            logger.warning("Monitoring is already running")
            return

        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"Started InfluxDB monitoring (interval: {self._monitoring_interval}s)")

    async def stop_monitoring(self):
        """
        Stop the monitoring loop.
        停止監控循環。
        """
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped InfluxDB monitoring")

    async def _monitoring_loop(self):
        """
        Main monitoring loop.
        主監控循環。
        """
        while True:
            try:
                # Run health checks
                await self.run_health_checks()

                # Write metrics to InfluxDB
                await self.write_metrics_to_influxdb()

                # Sleep until next check
                await asyncio.sleep(self._monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)  # Short sleep on error

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all metrics.
        獲取所有指標的摘要。
        """
        summary = {
            "operations": {
                "total_writes": self.total_writes,
                "total_reads": self.total_reads,
                "total_errors": self.total_errors,
                "last_operation": self.last_operation_time.isoformat() if self.last_operation_time else None
            },
            "operation_counts": dict(self.operation_counts),
            "operation_errors": dict(self.operation_errors),
            "health_status": {
                component: {
                    "status": health.status,
                    "message": health.message,
                    "timestamp": health.timestamp.isoformat(),
                    "metrics": health.metrics
                }
                for component, health in self.health_status.items()
            }
        }

        # Calculate performance statistics
        if self.operation_metrics:
            durations = [m.duration for m in self.operation_metrics if m.duration]
            if durations:
                summary["performance"] = {
                    "avg_operation_time_ms": sum(durations) / len(durations),
                    "min_operation_time_ms": min(durations),
                    "max_operation_time_ms": max(durations),
                    "operations_per_minute": len([m for m in self.operation_metrics
                                                  if m.end_time and
                                                  (datetime.utcnow() - m.end_time).total_seconds() < 60])
                }

        return summary

    def export_metrics(self, format: str = "json") -> str:
        """
        Export metrics in specified format.
        以指定格式導出指標。
        """
        metrics = self.get_metrics_summary()

        if format.lower() == "json":
            return json.dumps(metrics, indent=2)
        elif format.lower() == "prometheus":
            # Convert to Prometheus format
            prometheus_lines = []

            # Operation counts
            for op, count in metrics["operation_counts"].items():
                prometheus_lines.append(f"influxdb_operations_total{{operation="{op}"}} {count}")

            # Health status
            for component, health in metrics["health_status"].items():
                status_value = 1 if health["status"] == "healthy" else (0.5 if health["status"] == "degraded" else 0)
                prometheus_lines.append(f"influxdb_component_healthy{{component="{component}"}} {status_value}")

            return "\n".join(prometheus_lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Example usage and testing
async def test_monitoring():
    """Test the monitoring functionality"""
    from .influxdb_client import InfluxDBManager, InfluxDBConfig

    # Create manager and monitor
    config = InfluxDBConfig()
    manager = InfluxDBManager(config)
    await manager.initialize()

    monitor = InfluxDBMonitor(manager)

    # Start monitoring
    await monitor.start_monitoring()

    try:
        # Simulate some operations
        for i in range(10):
            @monitor.track_operation("test_operation")
            async def test_func():
                await asyncio.sleep(0.1)
                if i % 5 == 0:
                    raise Exception("Test error")
                return f"result_{i}"

            try:
                await test_func()
            except:
                pass

        # Wait a bit for monitoring
        await asyncio.sleep(2)

        # Get metrics summary
        summary = monitor.get_metrics_summary()
        print("Metrics Summary:")
        print(json.dumps(summary, indent=2))

        # Export metrics
        print("\nPrometheus Export:")
        print(monitor.export_metrics("prometheus"))

    finally:
        await monitor.stop_monitoring()
        await manager.close()


if __name__ == "__main__":
    asyncio.run(test_monitoring())
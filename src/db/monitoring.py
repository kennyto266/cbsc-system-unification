"""
Database Performance Monitoring

Provides monitoring and metrics collection for database operations.
"""

import logging
import time
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any

from sqlalchemy import event, Engine
from sqlalchemy.engine import Engine as SQLEngine

logger = logging.getLogger(__name__)


class QueryMetrics:
    """Individual query metrics"""

    def __init__(
        self,
        statement: str,
        duration: float,
        parameters: Any = None
    ):
        self.statement = statement
        self.duration = duration
        self.parameters = parameters
        self.timestamp = datetime.now(timezone.utc)

    @property
    def is_slow(self, threshold: float = 1.0) -> bool:
        """Check if query is slow"""
        return self.duration > threshold

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "statement": self.statement[:200],  # Truncate long statements
            "duration_ms": round(self.duration * 1000, 2),
            "timestamp": self.timestamp.isoformat(),
            "is_slow": self.is_slow()
        }


class DatabasePerformanceMonitor:
    """Database performance monitoring system"""

    def __init__(self, slow_query_threshold: float = 1.0):
        """
        Initialize performance monitor.

        Args:
            slow_query_threshold: Threshold for slow query detection (seconds)
        """
        self.slow_query_threshold = slow_query_threshold
        self.query_history: List[QueryMetrics] = []
        self.max_history = 1000
        self.query_stats = defaultdict(lambda: {
            "count": 0,
            "total_duration": 0.0,
            "max_duration": 0.0,
            "slow_count": 0
        })
        self.logger = logging.getLogger(__name__)

    def setup_monitoring(self, engine: Engine):
        """
        Setup event listeners for monitoring.

        Args:
            engine: SQLAlchemy engine
        """
        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Record query start time"""
            context._query_start_time = time.time()

        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Record query metrics"""
            duration = time.time() - context._query_start_time

            metrics = QueryMetrics(statement, duration, parameters)
            self._record_query(metrics)

            if metrics.is_slow(self.slow_query_threshold):
                self.logger.warning(
                    f"Slow query ({duration:.3f}s): {statement[:200]}..."
                )

        @event.listens_for(engine, "handle_error")
        def handle_error(exception):
            """Log database errors"""
            self.logger.error(f"Database error: {exception}")

    def _record_query(self, metrics: QueryMetrics):
        """Record query metrics"""
        # Add to history
        self.query_history.append(metrics)
        if len(self.query_history) > self.max_history:
            self.query_history.pop(0)

        # Update statistics
        statement_hash = hash(metrics.statement)
        stats = self.query_stats[statement_hash]
        stats["count"] += 1
        stats["total_duration"] += metrics.duration
        stats["max_duration"] = max(stats["max_duration"], metrics.duration)
        if metrics.is_slow(self.slow_query_threshold):
            stats["slow_count"] += 1

    def get_query_stats(self, limit: int = 10) -> List[dict]:
        """
        Get query statistics.

        Args:
            limit: Maximum number of queries to return

        Returns:
            List of query statistics
        """
        stats_list = []
        for statement_hash, stats in self.query_stats.items():
            avg_duration = stats["total_duration"] / stats["count"] if stats["count"] > 0 else 0
            stats_list.append({
                "avg_duration_ms": round(avg_duration * 1000, 2),
                "max_duration_ms": round(stats["max_duration"] * 1000, 2),
                "count": stats["count"],
                "slow_count": stats["slow_count"],
                "slow_rate": round(stats["slow_count"] / stats["count"], 2) if stats["count"] > 0 else 0
            })

        # Sort by total duration
        stats_list.sort(key=lambda x: x["count"], reverse=True)
        return stats_list[:limit]

    def get_slow_queries(self, min_duration: float = None) -> List[QueryMetrics]:
        """
        Get slow queries.

        Args:
            min_duration: Minimum duration threshold

        Returns:
            List of slow query metrics
        """
        threshold = min_duration or self.slow_query_threshold
        return [q for q in self.query_history if q.duration >= threshold]

    def get_recent_queries(self, limit: int = 50) -> List[QueryMetrics]:
        """Get recent queries"""
        return self.query_history[-limit:]

    def get_summary(self) -> dict:
        """Get performance summary"""
        total_queries = len(self.query_history)
        slow_queries = self.get_slow_queries()

        if total_queries == 0:
            return {
                "total_queries": 0,
                "avg_duration_ms": 0,
                "max_duration_ms": 0,
                "slow_queries": 0,
                "slow_rate": 0
            }

        total_duration = sum(q.duration for q in self.query_history)
        max_duration = max(q.duration for q in self.query_history)

        return {
            "total_queries": total_queries,
            "avg_duration_ms": round((total_duration / total_queries) * 1000, 2),
            "max_duration_ms": round(max_duration * 1000, 2),
            "slow_queries": len(slow_queries),
            "slow_rate": round(len(slow_queries) / total_queries, 2),
            "unique_queries": len(self.query_stats)
        }

    def reset(self):
        """Reset all metrics"""
        self.query_history.clear()
        self.query_stats.clear()


class ConnectionPoolMonitor:
    """Monitor database connection pool metrics"""

    def __init__(self):
        self.pool_stats = []
        self.logger = logging.getLogger(__name__)

    def record_pool_stats(self, pool_info: dict):
        """Record pool statistics"""
        pool_info["timestamp"] = datetime.now(timezone.utc)
        self.pool_stats.append(pool_info)

        # Keep only last 1000 records
        if len(self.pool_stats) > 1000:
            self.pool_stats.pop(0)

    def get_pool_stats(self) -> dict:
        """Get current pool statistics"""
        if not self.pool_stats:
            return {
                "status": "no_data",
                "message": "No pool statistics recorded"
            }

        latest = self.pool_stats[-1]

        # Calculate trends
        if len(self.pool_stats) > 1:
            prev = self.pool_stats[-2]
            return {
                "current": latest,
                "trends": {
                    "checked_in": latest.get("checked_in", 0) - prev.get("checked_in", 0),
                    "checked_out": latest.get("checked_out", 0) - prev.get("checked_out", 0),
                    "overflow": latest.get("overflow", 0) - prev.get("overflow", 0)
                }
            }

        return {"current": latest}

    def get_pool_utilization(self) -> dict:
        """Get pool utilization metrics"""
        if not self.pool_stats:
            return {}

        latest = self.pool_stats[-1]
        pool_size = latest.get("pool_size", 1)
        checked_out = latest.get("checked_out", 0)
        overflow = latest.get("overflow", 0)

        return {
            "utilization_percent": round((checked_out / pool_size) * 100, 2) if pool_size > 0 else 0,
            "active_connections": checked_out,
            "overflow_connections": overflow,
            "available_connections": pool_size - checked_out
        }


@contextmanager
def monitor_query_performance(monitor: DatabasePerformanceMonitor):
    """Context manager for monitoring query performance during a block"""
    start_time = time.time()

    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.debug(f"Query block completed in {duration:.3f}s")


class DatabaseHealthChecker:
    """Health checker for database operations"""

    def __init__(self, connection_manager):
        """
        Initialize health checker.

        Args:
            connection_manager: DatabaseConnectionManager instance
        """
        self.connection_manager = connection_manager
        self.check_history = []
        self.logger = logging.getLogger(__name__)

    def check_health(self) -> dict:
        """
        Perform comprehensive health check.

        Returns:
            Health check results
        """
        start_time = time.time()

        # Check database connectivity
        db_health = self.connection_manager.health_check()

        # Check connection pool
        pool_monitor = ConnectionPoolMonitor()
        if "checked_in" in db_health:
            pool_monitor.record_pool_stats(db_health)
        pool_utilization = pool_monitor.get_pool_utilization()

        # Calculate total check duration
        check_duration = time.time() - start_time

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "healthy" if db_health.get("status") == "healthy" else "unhealthy",
            "check_duration_ms": round(check_duration * 1000, 2),
            "database": db_health,
            "pool_utilization": pool_utilization
        }

        # Record to history
        self.check_history.append(result)
        if len(self.check_history) > 100:
            self.check_history.pop(0)

        return result

    def get_health_trend(self, minutes: int = 5) -> dict:
        """
        Get health trend over time.

        Args:
            minutes: Time period to analyze

        Returns:
            Health trend statistics
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)

        recent_checks = [
            c for c in self.check_history
            if datetime.fromisoformat(c["timestamp"]) > cutoff_time
        ]

        if not recent_checks:
            return {"status": "no_data", "message": "No recent health checks"}

        healthy_count = sum(1 for c in recent_checks if c["status"] == "healthy")

        avg_check_duration = sum(
            c["check_duration_ms"] for c in recent_checks
        ) / len(recent_checks)

        return {
            "total_checks": len(recent_checks),
            "healthy_checks": healthy_count,
            "unhealthy_checks": len(recent_checks) - healthy_count,
            "health_rate": round(healthy_count / len(recent_checks), 2),
            "avg_check_duration_ms": round(avg_check_duration, 2)
        }


# Global monitoring instance
_global_monitor: Optional[DatabasePerformanceMonitor] = None
_global_health_checker: Optional[DatabaseHealthChecker] = None


def get_monitor() -> DatabasePerformanceMonitor:
    """Get global performance monitor"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = DatabasePerformanceMonitor()
    return _global_monitor


def get_health_checker(connection_manager=None) -> DatabaseHealthChecker:
    """Get global health checker"""
    global _global_health_checker

    if _global_health_checker is None:
        if connection_manager is None:
            raise ValueError("connection_manager required for first initialization")
        _global_health_checker = DatabaseHealthChecker(connection_manager)

    return _global_health_checker


def setup_monitoring(
    engine: Engine,
    slow_query_threshold: float = 1.0
) -> DatabasePerformanceMonitor:
    """
    Setup database performance monitoring.

    Args:
        engine: SQLAlchemy engine
        slow_query_threshold: Threshold for slow query detection

    Returns:
        DatabasePerformanceMonitor instance
    """
    global _global_monitor

    _global_monitor = DatabasePerformanceMonitor(
        slow_query_threshold=slow_query_threshold
    )
    _global_monitor.setup_monitoring(engine)

    return _global_monitor

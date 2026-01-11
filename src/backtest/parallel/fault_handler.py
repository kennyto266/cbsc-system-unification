"""
Fault Tolerance and Recovery System for CBSC multiprocessing backtesting.

Provides comprehensive error handling, automatic recovery, and health monitoring
for the distributed backtesting system.
"""

import time
import logging
import threading
import signal
import traceback
from typing import Dict, List, Any, Optional, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import TimeoutError, Future
import psutil
import gc
from collections import defaultdict, deque

from .models import Task, TaskResult, ProcessInfo


class ErrorType(str, Enum):
    """Types of errors that can occur."""
    TIMEOUT = "timeout"
    MEMORY_ERROR = "memory_error"
    PROCESS_CRASH = "process_crash"
    SERIALIZATION_ERROR = "serialization_error"
    DEADLOCK = "deadlock"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


class RecoveryAction(str, Enum):
    """Recovery actions to take."""
    RETRY = "retry"
    RESTART_PROCESS = "restart_process"
    SCALE_RESOURCES = "scale_resources"
    FAIL_FAST = "fail_fast"
    CIRCUIT_BREAKER = "circuit_breaker"
    GRACEFUL_DEGRADATION = "graceful_degradation"


@dataclass
class ErrorReport:
    """Detailed error report."""
    task_id: Optional[str]
    process_id: Optional[int]
    error_type: ErrorType
    error_message: str
    traceback_info: str
    timestamp: float = field(default_factory=time.time)
    severity: str = "medium"  # low, medium, high, critical
    recovery_action: RecoveryAction = RecoveryAction.RETRY
    retry_count: int = 0
    max_retries: int = 3
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthStatus:
    """Health status of a component."""
    component_id: str
    is_healthy: bool
    last_check: float = field(default_factory=time.time)
    error_count: int = 0
    max_errors: int = 10
    recovery_attempts: int = 0
    last_recovery: Optional[float] = None
    metrics: Dict[str, float] = field(default_factory=dict)


class CircuitBreaker:
    """Circuit breaker pattern implementation."""

    def __init__(self,
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 expected_exception: Type[Exception] = Exception):

        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half_open

    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap function with circuit breaker."""
        def wrapper(*args, **kwargs):
            if self.state == "open":
                if self._should_attempt_reset():
                    self.state = "half_open"
                else:
                    raise Exception("Circuit breaker is open")

            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result

            except self.expected_exception as e:
                self._on_failure()
                raise e

        return wrapper

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker."""
        return (self.last_failure_time and
                time.time() - self.last_failure_time >= self.recovery_timeout)

    def _on_success(self):
        """Handle successful execution."""
        self.failure_count = 0
        self.state = "closed"

    def _on_failure(self):
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"


class ResourceMonitor:
    """Monitor system resources and detect issues."""

    def __init__(self, check_interval: float = 5.0):
        self.check_interval = check_interval
        self.logger = logging.getLogger(f"{__name__}.ResourceMonitor")
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.callbacks: Dict[str, List[Callable]] = defaultdict(list)

        # Thresholds
        self.cpu_threshold = 90.0
        self.memory_threshold = 85.0
        self.disk_threshold = 90.0

    def start_monitoring(self):
        """Start resource monitoring."""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Resource monitoring started")

    def stop_monitoring(self):
        """Stop resource monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        self.logger.info("Resource monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                metrics = self._collect_metrics()
                self._check_thresholds(metrics)
                time.sleep(self.check_interval)

            except Exception as e:
                self.logger.error(f"Error in resource monitoring: {e}")

    def _collect_metrics(self) -> Dict[str, float]:
        """Collect system resource metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent

        # Process count
        process_count = len(psutil.pids())

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_percent": disk_percent,
            "process_count": process_count,
            "memory_available_gb": memory.available / (1024**3)
        }

    def _check_thresholds(self, metrics: Dict[str, float]):
        """Check if any metrics exceed thresholds."""
        alerts = []

        if metrics["cpu_percent"] > self.cpu_threshold:
            alerts.append(f"CPU usage high: {metrics['cpu_percent']:.1f}%")

        if metrics["memory_percent"] > self.memory_threshold:
            alerts.append(f"Memory usage high: {metrics['memory_percent']:.1f}%")

        if metrics["disk_percent"] > self.disk_threshold:
            alerts.append(f"Disk usage high: {metrics['disk_percent']:.1f}%")

        if alerts:
            for callback in self.callbacks["alert"]:
                try:
                    callback(alerts, metrics)
                except Exception as e:
                    self.logger.error(f"Error in alert callback: {e}")

    def add_alert_callback(self, callback: Callable[[List[str], Dict[str, float]], None]):
        """Add callback for resource alerts."""
        self.callbacks["alert"].append(callback)


class RetryPolicy:
    """Retry policy configuration."""

    def __init__(self,
                 max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 exponential_base: float = 2.0,
                 jitter: bool = True):

        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt."""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            # Add ±25% jitter
            jitter_range = delay * 0.25
            import random
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)


class TaskRetryManager:
    """Manages task retry logic with exponential backoff."""

    def __init__(self, retry_policy: Optional[RetryPolicy] = None):
        self.retry_policy = retry_policy or RetryPolicy()
        self.logger = logging.getLogger(f"{__name__}.TaskRetryManager")
        self.retry_history: Dict[str, List[ErrorReport]] = defaultdict(list)

    def should_retry(self, error_report: ErrorReport) -> bool:
        """Determine if a task should be retried."""
        if error_report.retry_count >= error_report.max_retries:
            return False

        # Don't retry certain error types
        non_retryable_errors = {
            ErrorType.MEMORY_ERROR,
            ErrorType.DEADLOCK,
            ErrorType.SERIALIZATION_ERROR
        }

        if error_report.error_type in non_retryable_errors:
            return False

        return True

    def schedule_retry(self, error_report: ErrorReport, retry_callback: Callable):
        """Schedule a task retry with appropriate delay."""
        delay = self.retry_policy.get_delay(error_report.retry_count)

        self.logger.info(f"Scheduling retry for task {error_report.task_id} "
                        f"after {delay:.2f}s (attempt {error_report.retry_count + 1})")

        # Store retry history
        self.retry_history[error_report.task_id].append(error_report)

        # Schedule retry in background
        def retry_wrapper():
            time.sleep(delay)
            try:
                retry_callback(error_report.task_id)
            except Exception as e:
                self.logger.error(f"Retry callback failed: {e}")

        retry_thread = threading.Thread(target=retry_wrapper, daemon=True)
        retry_thread.start()

    def get_retry_history(self, task_id: str) -> List[ErrorReport]:
        """Get retry history for a task."""
        return self.retry_history[task_id].copy()


class FaultHandler:
    """
    Comprehensive fault tolerance and recovery system.

    Features:
    - Automatic task retry with exponential backoff
    - Process health monitoring and recovery
    - Circuit breaker pattern implementation
    - Resource monitoring and alerting
    - Graceful degradation strategies
    """

    def __init__(self,
                 enable_circuit_breaker: bool = True,
                 enable_resource_monitoring: bool = True,
                 retry_policy: Optional[RetryPolicy] = None):

        self.logger = logging.getLogger(f"{__name__}.FaultHandler")

        # Components
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.enable_circuit_breaker = enable_circuit_breaker
        self.resource_monitor = ResourceMonitor() if enable_resource_monitoring else None
        self.retry_manager = TaskRetryManager(retry_policy)

        # State tracking
        self.process_health: Dict[int, HealthStatus] = {}
        self.error_reports: List[ErrorReport] = []
        self.recovery_callbacks: Dict[str, List[Callable]] = defaultdict(list)

        # Statistics
        self.total_errors = 0
        self.total_recoveries = 0
        self.total_retries = 0

        # Thread safety
        self.lock = threading.RLock()

        # Setup
        self._setup_signal_handlers()

    def start(self):
        """Start the fault handler."""
        with self.lock:
            if self.resource_monitor:
                self.resource_monitor.add_alert_callback(self._handle_resource_alert)
                self.resource_monitor.start_monitoring()

            self.logger.info("Fault handler started")

    def stop(self):
        """Stop the fault handler."""
        with self.lock:
            if self.resource_monitor:
                self.resource_monitor.stop_monitoring()

            self.logger.info("Fault handler stopped")

    def register_process(self, process_info: ProcessInfo):
        """Register a process for health monitoring."""
        with self.lock:
            health_status = HealthStatus(
                component_id=f"process_{process_info.id}",
                is_healthy=True,
                max_errors=5
            )

            self.process_health[process_info.id] = health_status
            self.logger.debug(f"Registered process {process_info.id} for health monitoring")

    def unregister_process(self, process_id: int):
        """Unregister a process from health monitoring."""
        with self.lock:
            if process_id in self.process_health:
                del self.process_health[process_id]
                self.logger.debug(f"Unregistered process {process_id}")

    def handle_error(self,
                    task_id: Optional[str],
                    process_id: Optional[int],
                    error: Exception,
                    context: Optional[Dict[str, Any]] = None) -> ErrorReport:
        """
        Handle an error and determine recovery action.

        Returns:
            ErrorReport with recovery action
        """
        with self.lock:
            self.total_errors += 1

            # Classify error
            error_type = self._classify_error(error)
            severity = self._assess_severity(error, error_type)
            recovery_action = self._determine_recovery_action(error_type, severity)

            # Create error report
            error_report = ErrorReport(
                task_id=task_id,
                process_id=process_id,
                error_type=error_type,
                error_message=str(error),
                traceback_info=traceback.format_exc(),
                severity=severity,
                recovery_action=recovery_action,
                context=context or {}
            )

            self.error_reports.append(error_report)

            # Update process health
            if process_id is not None and process_id in self.process_health:
                health = self.process_health[process_id]
                health.error_count += 1
                health.last_check = time.time()

                if health.error_count >= health.max_errors:
                    health.is_healthy = False
                    self._handle_unhealthy_process(process_id)

            # Log error
            log_level = {
                "low": logging.INFO,
                "medium": logging.WARNING,
                "high": logging.ERROR,
                "critical": logging.CRITICAL
            }.get(severity, logging.ERROR)

            self.logger.log(log_level, f"Error handled: {error_report.error_message}")

            # Trigger recovery
            self._trigger_recovery(error_report)

            return error_report

    def retry_task(self,
                  task_id: str,
                  retry_callback: Callable[[str], None],
                  max_retries: int = 3) -> bool:
        """
        Schedule a task for retry.

        Returns:
            True if retry scheduled, False if not
        """
        with self.lock:
            # Find the most recent error for this task
            task_errors = [e for e in self.error_reports if e.task_id == task_id]
            if not task_errors:
                return False

            latest_error = max(task_errors, key=lambda e: e.timestamp)
            latest_error.max_retries = max_retries

            if self.retry_manager.should_retry(latest_error):
                self.total_retries += 1
                self.retry_manager.schedule_retry(latest_error, retry_callback)
                return True

            return False

    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify the type of error."""
        error_name = error.__class__.__name__.lower()
        error_message = str(error).lower()

        if "timeout" in error_name or "timeout" in error_message:
            return ErrorType.TIMEOUT
        elif "memory" in error_name or "memory" in error_message:
            return ErrorType.MEMORY_ERROR
        elif "deadlock" in error_name or "deadlock" in error_message:
            return ErrorType.DEADLOCK
        elif "serialization" in error_name or "pickle" in error_message:
            return ErrorType.SERIALIZATION_ERROR
        elif "connection" in error_name or "network" in error_message:
            return ErrorType.NETWORK_ERROR
        elif "resource" in error_name or "exhausted" in error_message:
            return ErrorType.RESOURCE_EXHAUSTION
        elif "process" in error_name or "crash" in error_message:
            return ErrorType.PROCESS_CRASH
        else:
            return ErrorType.UNKNOWN

    def _assess_severity(self, error: Exception, error_type: ErrorType) -> str:
        """Assess error severity."""
        # High severity errors
        if error_type in {ErrorType.MEMORY_ERROR, ErrorType.DEADLOCK, ErrorType.PROCESS_CRASH}:
            return "high"

        # Critical errors
        if "critical" in str(error).lower() or "fatal" in str(error).lower():
            return "critical"

        # Medium severity errors
        if error_type in {ErrorType.TIMEOUT, ErrorType.RESOURCE_EXHAUSTION}:
            return "medium"

        # Default to low severity
        return "low"

    def _determine_recovery_action(self, error_type: ErrorType, severity: str) -> RecoveryAction:
        """Determine the appropriate recovery action."""
        if severity == "critical":
            return RecoveryAction.FAIL_FAST

        if error_type == ErrorType.TIMEOUT:
            return RecoveryAction.RETRY

        if error_type == ErrorType.MEMORY_ERROR:
            return RecoveryAction.SCALE_RESOURCES

        if error_type == ErrorType.PROCESS_CRASH:
            return RecoveryAction.RESTART_PROCESS

        if error_type in {ErrorType.NETWORK_ERROR, ErrorType.SERIALIZATION_ERROR}:
            return RecoveryAction.RETRY

        return RecoveryAction.RETRY

    def _trigger_recovery(self, error_report: ErrorReport):
        """Trigger the appropriate recovery action."""
        action = error_report.recovery_action

        if action == RecoveryAction.RETRY and error_report.task_id:
            self._schedule_retry(error_report)

        elif action == RecoveryAction.RESTART_PROCESS and error_report.process_id:
            self._restart_process(error_report.process_id)

        elif action == RecoveryAction.SCALE_RESOURCES:
            self._scale_resources()

        elif action == RecoveryAction.CIRCUIT_BREAKER:
            self._activate_circuit_breaker(error_report)

        # Notify callbacks
        for callback in self.recovery_callbacks[action]:
            try:
                callback(error_report)
            except Exception as e:
                self.logger.error(f"Error in recovery callback: {e}")

    def _schedule_retry(self, error_report: ErrorReport):
        """Schedule a task retry."""
        def retry_callback(task_id: str):
            # This would be handled by the task distributor
            self.logger.info(f"Retry scheduled for task {task_id}")

        if self.retry_manager.schedule_retry(error_report, retry_callback):
            self.total_recoveries += 1

    def _restart_process(self, process_id: int):
        """Restart a failed process."""
        self.logger.info(f"Restarting process {process_id}")
        self.total_recoveries += 1

        # Update health status
        if process_id in self.process_health:
            health = self.process_health[process_id]
            health.recovery_attempts += 1
            health.last_recovery = time.time()

        # In a real implementation, this would coordinate with the process pool

    def _scale_resources(self):
        """Scale system resources to handle load."""
        self.logger.warning("Scaling resources due to memory/exhaustion errors")

        # Force garbage collection
        gc.collect()

        # In a real implementation, this might:
        # 1. Request more processes
        # 2. Increase memory limits
        # 3. Activate resource-saving modes

    def _activate_circuit_breaker(self, error_report: ErrorReport):
        """Activate circuit breaker for failing component."""
        component_id = f"process_{error_report.process_id}" if error_report.process_id else "default"

        if component_id not in self.circuit_breakers:
            self.circuit_breakers[component_id] = CircuitBreaker()

        self.logger.warning(f"Activating circuit breaker for {component_id}")

    def _handle_unhealthy_process(self, process_id: int):
        """Handle an unhealthy process."""
        self.logger.error(f"Process {process_id} marked as unhealthy")

        # In a real implementation, this might:
        # 1. Stop accepting new tasks
        # 2. Wait for current tasks to complete
        # 3. Restart the process
        # 4. Redistribute pending tasks

    def _handle_resource_alert(self, alerts: List[str], metrics: Dict[str, float]):
        """Handle resource monitoring alerts."""
        self.logger.warning(f"Resource alerts: {alerts}")

        # Trigger appropriate recovery actions
        if metrics["memory_percent"] > 95:
            self._scale_resources()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown")
            self.stop()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    def add_recovery_callback(self, action: RecoveryAction, callback: Callable[[ErrorReport], None]):
        """Add callback for specific recovery actions."""
        self.recovery_callbacks[action].append(callback)

    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report."""
        with self.lock:
            healthy_processes = sum(1 for h in self.process_health.values() if h.is_healthy)
            total_processes = len(self.process_health)

            recent_errors = [
                e for e in self.error_reports
                if time.time() - e.timestamp < 3600  # Last hour
            ]

            return {
                "overall_health": healthy_processes / max(1, total_processes),
                "processes": {
                    "total": total_processes,
                    "healthy": healthy_processes,
                    "unhealthy": total_processes - healthy_processes
                },
                "errors": {
                    "total": self.total_errors,
                    "recent": len(recent_errors),
                    "by_type": self._count_errors_by_type(recent_errors),
                    "by_severity": self._count_errors_by_severity(recent_errors)
                },
                "recoveries": {
                    "total": self.total_recoveries,
                    "retries": self.total_retries,
                    "success_rate": self.total_recoveries / max(1, self.total_errors)
                },
                "circuit_breakers": {
                    "active": len(self.circuit_breakers),
                    "states": {k: v.state for k, v in self.circuit_breakers.items()}
                }
            }

    def _count_errors_by_type(self, errors: List[ErrorReport]) -> Dict[str, int]:
        """Count errors by type."""
        counts = defaultdict(int)
        for error in errors:
            counts[error.error_type] += 1
        return dict(counts)

    def _count_errors_by_severity(self, errors: List[ErrorReport]) -> Dict[str, int]:
        """Count errors by severity."""
        counts = defaultdict(int)
        for error in errors:
            counts[error.severity] += 1
        return dict(counts)
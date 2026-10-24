#!/usr/bin/env python3
"""
Memory Leak Detector for Production Environment
Advanced leak detection and prevention system for 32-core parallel processing

This module provides production-grade memory leak detection capabilities that
address the unbounded memory growth issues identified in the stability analysis.

Key Features:
- Real-time memory leak detection with configurable thresholds
- Multi-process leak monitoring
- Object reference tracking and analysis
- Automatic leak prevention and cleanup
- Production alerting and reporting
- Integration with adaptive memory allocator
"""

import os
import sys
import gc
import time
import threading
import logging
import psutil
import tracemalloc
import weakref
import inspect
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import pickle
from collections import defaultdict, deque
import traceback

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


class LeakSeverity(Enum):
    """Memory leak severity levels"""
    LOW = "low"          # < 50MB increase
    MEDIUM = "medium"    # 50-100MB increase
    HIGH = "high"        # 100-500MB increase
    CRITICAL = "critical" # > 500MB increase


class LeakStatus(Enum):
    """Memory leak status"""
    MONITORING = "monitoring"      # Currently monitoring
    DETECTED = "detected"          # Leak detected
    INVESTIGATING = "investigating" # Investigating source
    CONTAINED = "contained"        # Leak contained/cleaned
    RESOLVED = "resolved"          # Leak resolved


@dataclass
class MemorySnapshot:
    """Memory usage snapshot at a point in time"""
    timestamp: datetime
    pid: int
    process_name: str
    memory_rss_mb: float
    memory_vms_mb: float
    memory_percent: float
    object_count: int
    gc_objects: int
    tracemalloc_current: int
    tracemalloc_peak: int


@dataclass
class LeakAlert:
    """Memory leak alert information"""
    timestamp: datetime
    severity: LeakSeverity
    pid: int
    process_name: str
    memory_increase_mb: float
    time_window_minutes: float
    growth_rate_mb_per_minute: float
    status: LeakStatus
    suspected_sources: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    investigation_notes: str = ""
    resolution_time: Optional[datetime] = None


@dataclass
class ObjectTrackingInfo:
    """Information about tracked objects"""
    object_id: int
    object_type: str
    size_bytes: int
    creation_time: datetime
    ref_count: int
    traceback_info: str
    is_alive: bool


class MemoryLeakDetector:
    """
    Production-grade Memory Leak Detection System

    This class provides comprehensive memory leak detection and prevention
    capabilities for high-performance parallel processing environments.

    Key Features:
    - Real-time monitoring of multiple processes
    - Intelligent leak detection with configurable thresholds
    - Automatic object reference tracking
    - Production alerting and reporting
    - Integration with cleanup mechanisms
    """

    def __init__(
        self,
        detection_threshold_mb: float = 100.0,
        monitoring_interval: float = 30.0,
        time_window_minutes: float = 10.0,
        enable_object_tracking: bool = True,
        enable_tracemalloc: bool = True,
        max_tracked_objects: int = 10000,
        alert_cooldown_minutes: float = 5.0,
        auto_cleanup_threshold_mb: float = 500.0
    ):
        """
        Initialize memory leak detector

        Args:
            detection_threshold_mb: Memory increase threshold for leak detection (MB)
            monitoring_interval: Monitoring interval in seconds
            time_window_minutes: Time window for leak detection (minutes)
            enable_object_tracking: Enable detailed object tracking
            enable_tracemalloc: Enable tracemalloc for detailed analysis
            max_tracked_objects: Maximum number of objects to track
            alert_cooldown_minutes: Cooldown period between alerts (minutes)
            auto_cleanup_threshold_mb: Threshold for automatic cleanup (MB)
        """
        self.detection_threshold_mb = detection_threshold_mb
        self.monitoring_interval = monitoring_interval
        self.time_window_minutes = time_window_minutes
        self.enable_object_tracking = enable_object_tracking
        self.enable_tracemalloc = enable_tracemalloc
        self.max_tracked_objects = max_tracked_objects
        self.alert_cooldown_minutes = alert_cooldown_minutes
        self.auto_cleanup_threshold_mb = auto_cleanup_threshold_mb

        # State tracking
        self.monitoring_active = False
        self.monitor_thread = None
        self.baseline_memory: Dict[int, MemorySnapshot] = {}
        self.memory_history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.leak_alerts: List[LeakAlert] = []
        self.tracked_objects: Dict[int, ObjectTrackingInfo] = {}
        self.last_alert_time: Dict[int, datetime] = {}

        # Statistics
        self.total_detections = 0
        self.false_positives = 0
        self.auto_cleanups = 0
        self.objects_tracked = 0

        # Feature flag integration
        self.feature_enabled = self._check_feature_flag()

        # Initialize tracking systems
        if self.enable_tracemalloc and not tracemalloc.is_tracing():
            tracemalloc.start()

        # Cleanup old data
        self._cleanup_old_data()

        logger.info(f"MemoryLeakDetector initialized with {detection_threshold_mb}MB threshold")

    def _check_feature_flag(self) -> bool:
        """Check if memory leak detection feature is enabled"""
        try:
            feature_config_path = Path(__file__).parent.parent / "config" / "feature_flags.yaml"
            if feature_config_path.exists():
                import yaml
                with open(feature_config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    return config.get('feature_flags', {}).get('enable_memory_leak_detection', False)
            return False
        except Exception as e:
            logger.warning(f"Could not check feature flag: {e}")
            return False

    def start_monitoring(self, target_processes: Optional[List[int]] = None):
        """
        Start memory leak monitoring

        Args:
            target_processes: List of PIDs to monitor (None for current process)
        """
        if self.monitoring_active:
            logger.warning("Memory leak monitoring already active")
            return

        if not self.feature_enabled:
            logger.info("Memory leak detection feature not enabled")
            return

        # Determine processes to monitor
        if target_processes is None:
            target_processes = [os.getpid()]
        else:
            target_processes = list(set(target_processes + [os.getpid()]))

        # Initialize baseline memory for all processes
        for pid in target_processes:
            try:
                snapshot = self._capture_memory_snapshot(pid)
                if snapshot:
                    self.baseline_memory[pid] = snapshot
                    logger.info(f"Monitoring process {pid} ({snapshot.process_name}) with {snapshot.memory_rss_mb:.1f}MB baseline")
            except Exception as e:
                logger.error(f"Failed to initialize monitoring for PID {pid}: {e}")

        # Start monitoring thread
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            name="MemoryLeakDetector",
            daemon=True
        )
        self.monitor_thread.start()

        logger.info(f"Memory leak monitoring started for {len(self.baseline_memory)} processes")

    def stop_monitoring(self):
        """Stop memory leak monitoring"""
        if not self.monitoring_active:
            return

        logger.info("Stopping memory leak monitoring...")
        self.monitoring_active = False

        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=10.0)

        logger.info("Memory leak monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                current_time = datetime.now()

                for pid in list(self.baseline_memory.keys()):
                    try:
                        # Capture current memory snapshot
                        snapshot = self._capture_memory_snapshot(pid)
                        if snapshot:
                            # Store in history
                            self.memory_history[pid].append(snapshot)

                            # Check for leaks
                            self._check_for_leaks(pid, snapshot, current_time)

                            # Update object tracking if enabled
                            if self.enable_object_tracking and pid == os.getpid():
                                self._update_object_tracking()

                    except psutil.NoSuchProcess:
                        logger.info(f"Process {pid} no longer exists, removing from monitoring")
                        del self.baseline_memory[pid]
                        if pid in self.memory_history:
                            del self.memory_history[pid]
                    except Exception as e:
                        logger.error(f"Error monitoring process {pid}: {e}")

                # Cleanup old data periodically
                if current_time.minute % 10 == 0:  # Every 10 minutes
                    self._cleanup_old_data()

                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Memory leak monitoring error: {e}")
                time.sleep(self.monitoring_interval)

    def _capture_memory_snapshot(self, pid: int) -> Optional[MemorySnapshot]:
        """Capture memory snapshot for a process"""
        try:
            process = psutil.Process(pid)
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()

            # Get object count for current process
            object_count = 0
            gc_objects = 0
            tracemalloc_current = 0
            tracemalloc_peak = 0

            if pid == os.getpid():
                object_count = len(gc.get_objects())
                gc_objects = len(gc.get_objects())
                if tracemalloc.is_tracing():
                    tracemalloc_current, tracemalloc_peak = tracemalloc.get_traced_memory()

            return MemorySnapshot(
                timestamp=datetime.now(),
                pid=pid,
                process_name=process.name(),
                memory_rss_mb=memory_info.rss / (1024 * 1024),
                memory_vms_mb=memory_info.vms / (1024 * 1024),
                memory_percent=memory_percent,
                object_count=object_count,
                gc_objects=gc_objects,
                tracemalloc_current=tracemalloc_current,
                tracemalloc_peak=tracemalloc_peak
            )

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"Cannot access process {pid}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to capture snapshot for PID {pid}: {e}")
            return None

    def _check_for_leaks(self, pid: int, current_snapshot: MemorySnapshot, current_time: datetime):
        """Check for memory leaks in a process"""
        baseline = self.baseline_memory.get(pid)
        if not baseline:
            return

        # Check if we have enough history
        history = self.memory_history[pid]
        if len(history) < 2:
            return

        # Calculate memory increase
        memory_increase = current_snapshot.memory_rss_mb - baseline.memory_rss_mb

        # Check time window
        time_diff_minutes = (current_snapshot.timestamp - baseline.timestamp).total_seconds() / 60

        if time_diff_minutes < self.time_window_minutes:
            return  # Not enough time has passed

        # Calculate growth rate
        growth_rate = memory_increase / time_diff_minutes

        # Check if threshold exceeded
        if memory_increase > self.detection_threshold_mb:
            self._handle_leak_detection(
                pid, current_snapshot, baseline,
                memory_increase, time_diff_minutes, growth_rate
            )

        # Check for auto-cleanup threshold
        if memory_increase > self.auto_cleanup_threshold_mb:
            self._trigger_auto_cleanup(pid, current_snapshot)

    def _handle_leak_detection(
        self,
        pid: int,
        current: MemorySnapshot,
        baseline: MemorySnapshot,
        memory_increase: float,
        time_diff_minutes: float,
        growth_rate: float
    ):
        """Handle detected memory leak"""
        # Check alert cooldown
        last_alert = self.last_alert_time.get(pid)
        if last_alert:
            cooldown_passed = (datetime.now() - last_alert).total_seconds() / 60
            if cooldown_passed < self.alert_cooldown_minutes:
                return  # Still in cooldown period

        # Determine severity
        if memory_increase > 500:
            severity = LeakSeverity.CRITICAL
        elif memory_increase > 100:
            severity = LeakSeverity.HIGH
        elif memory_increase > 50:
            severity = LeakSeverity.MEDIUM
        else:
            severity = LeakSeverity.LOW

        # Create leak alert
        alert = LeakAlert(
            timestamp=datetime.now(),
            severity=severity,
            pid=pid,
            process_name=current.process_name,
            memory_increase_mb=memory_increase,
            time_window_minutes=time_diff_minutes,
            growth_rate_mb_per_minute=growth_rate,
            status=LeakStatus.DETECTED,
            suspected_sources=self._identify_suspected_sources(pid),
            recommended_actions=self._generate_recommendations(memory_increase, growth_rate)
        )

        # Store alert
        self.leak_alerts.append(alert)
        self.last_alert_time[pid] = datetime.now()
        self.total_detections += 1

        # Log alert
        logger.warning(f"Memory leak detected in {current.process_name} (PID {pid}): "
                      f"+{memory_increase:.1f}MB in {time_diff_minutes:.1f}min "
                      f"({growth_rate:.1f}MB/min) - Severity: {severity.value}")

        # Trigger investigation if critical
        if severity == LeakSeverity.CRITICAL:
            self._trigger_investigation(alert)

    def _identify_suspected_sources(self, pid: int) -> List[str]:
        """Identify suspected sources of memory leak"""
        sources = []

        try:
            if pid == os.getpid() and self.enable_object_tracking:
                # Analyze object types with most growth
                object_type_counts = defaultdict(int)
                for obj in gc.get_objects():
                    obj_type = type(obj).__name__
                    object_type_counts[obj_type] += 1

                # Find top object types
                sorted_types = sorted(object_type_counts.items(), key=lambda x: x[1], reverse=True)
                for obj_type, count in sorted_types[:5]:
                    sources.append(f"High {obj_type} object count: {count}")

            # Add common leak sources
            if len(self.memory_history[pid]) > 10:
                recent_snapshots = list(self.memory_history[pid])[-10:]
                avg_growth = (recent_snapshots[-1].memory_rss_mb - recent_snapshots[0].memory_rss_mb) / len(recent_snapshots)
                if avg_growth > 10:  # > 10MB per snapshot on average
                    sources.append("Consistent memory growth pattern detected")

        except Exception as e:
            logger.error(f"Error identifying leak sources: {e}")
            sources.append("Error analyzing leak sources")

        return sources

    def _generate_recommendations(self, memory_increase: float, growth_rate: float) -> List[str]:
        """Generate recommendations for leak remediation"""
        recommendations = []

        if memory_increase > 500:
            recommendations.append("CRITICAL: Restart process immediately")
            recommendations.append("Check for unbounded data structures")
            recommendations.append("Review circular references")
        elif memory_increase > 100:
            recommendations.append("Review memory usage patterns")
            recommendations.append("Consider implementing memory limits")
            recommendations.append("Check for unreleased resources")

        if growth_rate > 50:  # > 50MB/min
            recommendations.append("High growth rate detected - investigate immediately")
            recommendations.append("Check for infinite loops or unbounded collections")

        recommendations.append("Review object lifecycle management")
        recommendations.append("Consider using weak references for cached objects")
        recommendations.append("Implement periodic memory cleanup")

        return recommendations

    def _trigger_investigation(self, alert: LeakAlert):
        """Trigger detailed investigation of memory leak"""
        logger.info(f"Triggering investigation for {alert.severity.value} leak in {alert.process_name}")

        try:
            # Analyze memory usage patterns
            if alert.pid == os.getpid() and tracemalloc.is_tracing():
                # Get tracemalloc statistics
                snapshot = tracemalloc.take_snapshot()
                top_stats = snapshot.statistics('lineno')

                logger.info("Top 10 memory allocations:")
                for i, stat in enumerate(top_stats[:10]):
                    logger.info(f"  {i+1}. {stat}")

            # Analyze object references
            if self.enable_object_tracking:
                self._analyze_object_references(alert)

            alert.status = LeakStatus.INVESTIGATING
            alert.investigation_notes = "Detailed analysis completed"

        except Exception as e:
            logger.error(f"Investigation failed: {e}")
            alert.investigation_notes = f"Investigation failed: {e}"

    def _analyze_object_references(self, alert: LeakAlert):
        """Analyze object references for leak sources"""
        try:
            # Find objects with many references
            ref_counts = defaultdict(int)
            for obj in gc.get_objects():
                ref_count = sys.getrefcount(obj)
                if ref_count > 100:  # Objects with unusually high reference counts
                    ref_counts[type(obj).__name__] += 1

            if ref_counts:
                logger.info("Objects with high reference counts:")
                for obj_type, count in sorted(ref_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                    logger.info(f"  {obj_type}: {count} objects")

        except Exception as e:
            logger.error(f"Object reference analysis failed: {e}")

    def _trigger_auto_cleanup(self, pid: int, snapshot: MemorySnapshot):
        """Trigger automatic memory cleanup"""
        logger.warning(f"Triggering automatic cleanup for PID {pid} due to excessive memory usage")

        try:
            # Force garbage collection
            collected = gc.collect()
            logger.info(f"Garbage collection completed: {collected} objects collected")

            # Clear caches if available
            self._clear_caches()

            # Compact memory pools
            if hasattr(self, '_compact_memory_pools'):
                self._compact_memory_pools()

            # Update baseline if memory was freed
            new_snapshot = self._capture_memory_snapshot(pid)
            if new_snapshot and new_snapshot.memory_rss_mb < snapshot.memory_rss_mb:
                freed_memory = snapshot.memory_rss_mb - new_snapshot.memory_rss_mb
                logger.info(f"Auto-cleanup freed {freed_memory:.1f}MB")
                self.baseline_memory[pid] = new_snapshot

            self.auto_cleanups += 1

        except Exception as e:
            logger.error(f"Auto-cleanup failed: {e}")

    def _clear_caches(self):
        """Clear various caches to free memory"""
        try:
            # Clear module caches
            import sys
            modules_to_clear = [name for name in sys.modules.keys() if name.startswith(('tempfile', 'urllib', 'http'))]
            for module_name in modules_to_clear:
                if module_name in sys.modules:
                    del sys.modules[module_name]

            # Clear function lru_cache
            import functools
            for obj in gc.get_objects():
                if hasattr(obj, 'cache_clear'):
                    try:
                        obj.cache_clear()
                    except:
                        pass

            logger.info("Cache cleanup completed")

        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")

    def _update_object_tracking(self):
        """Update object tracking information"""
        if not self.enable_object_tracking:
            return

        try:
            current_objects = gc.get_objects()
            current_time = datetime.now()

            # Track new objects
            for obj in current_objects[:self.max_tracked_objects]:  # Limit to prevent explosion
                obj_id = id(obj)

                if obj_id not in self.tracked_objects:
                    self.tracked_objects[obj_id] = ObjectTrackingInfo(
                        object_id=obj_id,
                        object_type=type(obj).__name__,
                        size_bytes=sys.getsizeof(obj),
                        creation_time=current_time,
                        ref_count=sys.getrefcount(obj),
                        traceback_info=self._get_object_traceback(obj),
                        is_alive=True
                    )
                    self.objects_tracked += 1
                else:
                    # Update existing object info
                    tracked = self.tracked_objects[obj_id]
                    tracked.is_alive = True
                    tracked.ref_count = sys.getrefcount(obj)

            # Clean up dead objects
            dead_objects = [obj_id for obj_id, info in self.tracked_objects.items() if not info.is_alive]
            for obj_id in dead_objects:
                del self.tracked_objects[obj_id]

            # Limit tracked objects
            if len(self.tracked_objects) > self.max_tracked_objects:
                # Keep only most recent objects
                sorted_objects = sorted(
                    self.tracked_objects.values(),
                    key=lambda x: x.creation_time,
                    reverse=True
                )
                self.tracked_objects = {
                    obj.object_id: obj for obj in sorted_objects[:self.max_tracked_objects]
                }

        except Exception as e:
            logger.error(f"Object tracking update failed: {e}")

    def _get_object_traceback(self, obj) -> str:
        """Get traceback information for object creation"""
        try:
            # Try to get frame information
            frame = inspect.currentframe()
            if frame:
                # Go up the call stack to find the creation site
                for _ in range(10):  # Limit depth
                    frame = frame.f_back
                    if frame and frame.f_code:
                        filename = Path(frame.f_code.co_filename).name
                        func_name = frame.f_code.co_name
                        lineno = frame.f_lineno
                        return f"{filename}:{func_name}:{lineno}"
        except Exception:
            pass

        return "unknown"

    def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        try:
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(hours=24)  # Keep 24 hours of data

            # Clean old alerts
            self.leak_alerts = [
                alert for alert in self.leak_alerts
                if alert.timestamp > cutoff_time
            ]

            # Clean old tracking data
            for pid in list(self.memory_history.keys()):
                history = self.memory_history[pid]
                while history and history[0].timestamp < cutoff_time:
                    history.popleft()

            # Clean old object tracking
            cutoff_time_objects = current_time - timedelta(hours=1)  # Keep 1 hour of object data
            dead_objects = [
                obj_id for obj_id, info in self.tracked_objects.items()
                if info.creation_time < cutoff_time_objects
            ]
            for obj_id in dead_objects:
                del self.tracked_objects[obj_id]

        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")

    def get_leak_report(self, pid: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate comprehensive leak detection report

        Args:
            pid: Process ID to generate report for (None for all processes)

        Returns:
            Dictionary containing leak detection statistics and alerts
        """
        # Filter alerts by PID if specified
        relevant_alerts = self.leak_alerts
        if pid is not None:
            relevant_alerts = [alert for alert in relevant_alerts if alert.pid == pid]

        # Calculate statistics
        severity_counts = defaultdict(int)
        status_counts = defaultdict(int)
        total_memory_leaked = 0

        for alert in relevant_alerts:
            severity_counts[alert.severity.value] += 1
            status_counts[alert.status.value] += 1
            total_memory_leaked += alert.memory_increase_mb

        # Get recent activity
        recent_alerts = [
            alert for alert in relevant_alerts
            if alert.timestamp > datetime.now() - timedelta(hours=24)
        ]

        return {
            'summary': {
                'total_alerts': len(relevant_alerts),
                'recent_alerts_24h': len(recent_alerts),
                'total_memory_leaked_mb': total_memory_leaked,
                'processes_monitored': len(self.baseline_memory),
                'total_detections': self.total_detections,
                'auto_cleanups': self.auto_cleanups,
                'objects_tracked': self.objects_tracked
            },
            'severity_distribution': dict(severity_counts),
            'status_distribution': dict(status_counts),
            'recent_alerts': [
                {
                    'timestamp': alert.timestamp.isoformat(),
                    'severity': alert.severity.value,
                    'process': alert.process_name,
                    'memory_increase_mb': alert.memory_increase_mb,
                    'growth_rate_mb_per_min': alert.growth_rate_mb_per_minute,
                    'status': alert.status.value
                }
                for alert in recent_alerts[-10:]  # Last 10 alerts
            ],
            'monitoring_status': {
                'active': self.monitoring_active,
                'interval_seconds': self.monitoring_interval,
                'detection_threshold_mb': self.detection_threshold_mb,
                'feature_enabled': self.feature_enabled
            }
        }

    def acknowledge_alert(self, alert_index: int, resolution_notes: str = "") -> bool:
        """
        Acknowledge and resolve a leak alert

        Args:
            alert_index: Index of alert to acknowledge
            resolution_notes: Notes about resolution

        Returns:
            True if alert was successfully acknowledged
        """
        try:
            if 0 <= alert_index < len(self.leak_alerts):
                alert = self.leak_alerts[alert_index]
                alert.status = LeakStatus.RESOLVED
                alert.resolution_time = datetime.now()
                if resolution_notes:
                    alert.investigation_notes += f"\nResolution: {resolution_notes}"
                logger.info(f"Alert {alert_index} acknowledged and resolved")
                return True
            else:
                logger.error(f"Invalid alert index: {alert_index}")
                return False
        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}")
            return False

    def reset_statistics(self):
        """Reset all detection statistics"""
        self.total_detections = 0
        self.false_positives = 0
        self.auto_cleanups = 0
        self.objects_tracked = 0
        self.leak_alerts.clear()
        self.tracked_objects.clear()
        logger.info("Memory leak detector statistics reset")


# Factory function for easy instantiation
def create_leak_detector(**kwargs) -> MemoryLeakDetector:
    """
    Factory function to create memory leak detector

    Args:
        **kwargs: Arguments for MemoryLeakDetector

    Returns:
        MemoryLeakDetector instance
    """
    return MemoryLeakDetector(**kwargs)


# Decorator for automatic leak detection in functions
def monitor_for_leaks(
    threshold_mb: float = 100.0,
    cleanup_on_exit: bool = True
):
    """
    Decorator to monitor functions for memory leaks

    Args:
        threshold_mb: Memory increase threshold in MB
        cleanup_on_exit: Whether to perform cleanup on function exit
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Create temporary detector
            detector = create_leak_detector(
                detection_threshold_mb=threshold_mb,
                monitoring_interval=1.0,
                time_window_minutes=1.0
            )

            # Get baseline memory
            baseline_memory = psutil.Process().memory_info().rss / (1024 * 1024)

            try:
                detector.start_monitoring()
                result = func(*args, **kwargs)
                return result
            finally:
                detector.stop_monitoring()

                if cleanup_on_exit:
                    gc.collect()

                # Check for leaks
                current_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                memory_increase = current_memory - baseline_memory

                if memory_increase > threshold_mb:
                    logger.warning(f"Potential memory leak detected in {func.__name__}: "
                                f"+{memory_increase:.1f}MB")

                detector.cleanup_old_data()

        return wrapper
    return decorator
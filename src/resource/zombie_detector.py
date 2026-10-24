#!/usr/bin/env python3
"""
Zombie Process Detector
Real-time zombie process detection and cleanup with psutil integration
"""

import os
import sys
import time
import signal
import logging
import threading
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import psutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


class ProcessState(Enum):
    """Process state categories"""
    RUNNING = "running"
    SLEEPING = "sleeping"
    ZOMBIE = "zombie"
    DEAD = "dead"
    UNKNOWN = "unknown"


@dataclass
class ZombieInfo:
    """Information about a detected zombie process"""
    pid: int
    ppid: int
    worker_id: Optional[int]
    detection_time: datetime
    process_name: str
    command_line: List[str]
    cpu_affinity: Optional[List[int]]
    memory_usage_mb: float
    creation_time: datetime
    status: str  # detected, cleaning, cleaned, failed
    cleanup_attempts: int = 0
    last_cleanup_attempt: Optional[datetime] = None
    cleanup_method: Optional[str] = None


@dataclass
class ZombieStats:
    """Statistics for zombie process detection and cleanup"""
    total_detected: int = 0
    total_cleaned: int = 0
    total_failed: int = 0
    detection_rate_per_minute: float = 0.0
    average_cleanup_time: float = 0.0
    current_active_zombies: int = 0
    peak_zombie_count: int = 0
    cleanup_success_rate: float = 0.0
    last_detection: Optional[datetime] = None
    last_cleanup: Optional[datetime] = None


@dataclass
class DetectorConfig:
    """Configuration for zombie process detector"""
    # Detection settings
    scan_interval: float = 2.0
    zombie_detection_threshold: int = 1  # Minutes of zombie state before action
    max_zombie_age_minutes: float = 10.0

    # Cleanup settings
    enable_auto_cleanup: bool = True
    cleanup_retry_attempts: int = 3
    cleanup_retry_delay: float = 1.0
    force_kill_timeout: float = 5.0

    # Process filtering
    target_process_names: List[str] = field(default_factory=lambda: ["python", "python3"])
    target_user: Optional[str] = None  # None = current user
    parent_pid_whitelist: List[int] = field(default_factory=list)

    # Alerting
    enable_alerting: bool = True
    alert_threshold_zombies: int = 5
    alert_cooldown_minutes: float = 5.0

    # Advanced settings
    enable_parent_tracking: bool = True
    enable_memory_tracking: bool = True
    enable_cpu_affinity_tracking: bool = True
    deep_process_inspection: bool = True


class ZombieProcessDetector:
    """
    Advanced zombie process detector with real-time monitoring and cleanup

    Features:
    - Real-time zombie process detection using psutil
    - Automatic zombie process reaping with multiple strategies
    - Process state monitoring and statistical tracking
    - Parent-child relationship tracking
    - Configurable detection thresholds and cleanup strategies
    - Comprehensive logging and alerting
    - Thread-safe operation for concurrent systems
    """

    def __init__(
        self,
        config: Optional[DetectorConfig] = None,
        managed_processes: Optional[Dict[int, int]] = None  # worker_id -> pid mapping
    ):
        self.config = config or DetectorConfig()
        self.managed_processes = managed_processes or {}

        # Detection state
        self.detected_zombies: Dict[int, ZombieInfo] = {}
        self.parent_child_map: Dict[int, Set[int]] = {}
        self.process_history: Dict[int, List[Tuple[datetime, str]]] = {}

        # Monitoring state
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.cleanup_thread: Optional[threading.Thread] = None

        # Statistics
        self.stats = ZombieStats()
        self.detection_history: List[Tuple[datetime, int]] = []  # (timestamp, zombie_count)
        self.cleanup_history: List[Tuple[datetime, float, bool]] = []  # (timestamp, duration, success)

        # Alerting state
        self.last_alert_time: Optional[datetime] = None
        self.alert_cooldown_active = False

        # Current user for filtering
        self.current_user = self.config.target_user or psutil.Process().username()

        logger.info("ZombieProcessDetector initialized")
        logger.info(f"Scan interval: {self.config.scan_interval}s, "
                   f"Auto cleanup: {self.config.enable_auto_cleanup}")

    def start_monitoring(self):
        """Start zombie process monitoring"""
        if self.monitoring_active:
            logger.warning("Zombie detector monitoring already active")
            return

        logger.info("Starting zombie process monitoring...")
        self.monitoring_active = True

        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            name="ZombieDetector",
            daemon=True
        )
        self.monitor_thread.start()

        # Start cleanup thread if auto-cleanup enabled
        if self.config.enable_auto_cleanup:
            self.cleanup_thread = threading.Thread(
                target=self._cleanup_loop,
                name="ZombieCleaner",
                daemon=True
            )
            self.cleanup_thread.start()

        logger.info("Zombie process monitoring started")

    def stop_monitoring(self):
        """Stop zombie process monitoring"""
        if not self.monitoring_active:
            return

        logger.info("Stopping zombie process monitoring...")
        self.monitoring_active = False

        # Wait for threads to finish
        for thread in [self.monitor_thread, self.cleanup_thread]:
            if thread and thread.is_alive():
                thread.join(timeout=5.0)

        logger.info("Zombie process monitoring stopped")

    def scan_for_zombies(self) -> List[ZombieInfo]:
        """
        Perform a scan for zombie processes

        Returns:
            List of newly detected zombie processes
        """
        newly_detected = []
        current_time = datetime.now()

        try:
            # Get all processes
            for proc in psutil.process_iter(['pid', 'ppid', 'name', 'cmdline', 'status', 'create_time', 'username']):
                try:
                    proc_info = proc.info

                    # Skip if process is not a zombie
                    if proc_info['status'] != psutil.STATUS_ZOMBIE:
                        continue

                    # Skip if not targeting this user
                    if proc_info['username'] != self.current_user:
                        continue

                    # Skip if not a target process name
                    if not any(name in proc_info.get('name', '') for name in self.config.target_process_names):
                        continue

                    pid = proc_info['pid']
                    ppid = proc_info['ppid']

                    # Skip if already detected
                    if pid in self.detected_zombies:
                        continue

                    # Create zombie info
                    zombie_info = ZombieInfo(
                        pid=pid,
                        ppid=ppid,
                        worker_id=self._find_worker_id(pid),
                        detection_time=current_time,
                        process_name=proc_info.get('name', 'unknown'),
                        command_line=proc_info.get('cmdline', []),
                        cpu_affinity=self._get_process_affinity(pid),
                        memory_usage_mb=self._get_process_memory(pid),
                        creation_time=datetime.fromtimestamp(proc_info.get('create_time', 0)),
                        status="detected"
                    )

                    # Add to detected zombies
                    self.detected_zombies[pid] = zombie_info
                    newly_detected.append(zombie_info)

                    # Update statistics
                    self.stats.total_detected += 1
                    self.stats.last_detection = current_time

                    # Update parent-child map
                    if self.config.enable_parent_tracking:
                        self.parent_child_map.setdefault(ppid, set()).add(pid)

                    # Update process history
                    self.process_history.setdefault(pid, []).append((current_time, "zombie_detected"))

                    logger.warning(f"Zombie process detected - PID: {pid}, PPID: {ppid}, "
                                 f"Name: {zombie_info.process_name}")

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception as e:
                    logger.debug(f"Error processing process info: {e}")
                    continue

            # Update statistics
            self.stats.current_active_zombies = len(self.detected_zombies)
            self.stats.peak_zombie_count = max(self.stats.peak_zombie_count, self.stats.current_active_zombies)

            # Calculate detection rate
            if self.detection_history:
                recent_detections = [
                    count for timestamp, count in self.detection_history[-30:]  # Last 30 entries
                ]
                if recent_detections:
                    self.stats.detection_rate_per_minute = sum(recent_detections) / 30.0 * (60.0 / self.config.scan_interval)

            # Add to detection history
            self.detection_history.append((current_time, len(newly_detected)))
            if len(self.detection_history) > 1000:  # Keep only recent history
                self.detection_history = self.detection_history[-1000:]

            # Check for alerting
            if self.config.enable_alerting:
                self._check_alert_conditions()

            if newly_detected:
                logger.info(f"Scan complete: {len(newly_detected)} new zombie processes detected")

            return newly_detected

        except Exception as e:
            logger.error(f"Error during zombie scan: {e}")
            return []

    def cleanup_zombie(self, pid: int, force: bool = False) -> bool:
        """
        Attempt to clean up a specific zombie process

        Args:
            pid: Process ID to clean up
            force: Force immediate cleanup

        Returns:
            True if cleanup successful
        """
        if pid not in self.detected_zombies:
            logger.warning(f"Zombie process {pid} not in detected list")
            return False

        zombie_info = self.detected_zombies[pid]
        cleanup_start_time = time.time()

        logger.info(f"Starting cleanup of zombie process {pid} (force: {force})")

        try:
            # Update zombie info
            zombie_info.status = "cleaning"
            zombie_info.cleanup_attempts += 1
            zombie_info.last_cleanup_attempt = datetime.now()

            cleanup_successful = False

            # Try different cleanup strategies
            if force or zombie_info.cleanup_attempts >= 2:
                # Force cleanup strategies
                cleanup_successful = self._force_cleanup_zombie(pid, zombie_info)
            else:
                # Gentle cleanup strategies
                cleanup_successful = self._gentle_cleanup_zombie(pid, zombie_info)

            # Record cleanup attempt
            cleanup_duration = time.time() - cleanup_start_time
            self.cleanup_history.append((datetime.now(), cleanup_duration, cleanup_successful))

            if cleanup_successful:
                zombie_info.status = "cleaned"
                zombie_info.cleanup_method = "success"

                # Remove from detected zombies
                del self.detected_zombies[pid]

                # Update statistics
                self.stats.total_cleaned += 1
                self.stats.current_active_zombies = len(self.detected_zombies)
                self.stats.last_cleanup = datetime.now()

                # Update average cleanup time
                successful_cleanups = [duration for _, duration, success in self.cleanup_history if success]
                if successful_cleanups:
                    self.stats.average_cleanup_time = sum(successful_cleanups) / len(successful_cleanups)

                # Update process history
                self.process_history[pid].append((datetime.now(), "zombie_cleaned"))

                logger.info(f"Successfully cleaned up zombie process {pid} in {cleanup_duration:.2f}s")

            else:
                zombie_info.status = "failed" if zombie_info.cleanup_attempts >= self.config.cleanup_retry_attempts else "detected"

                if zombie_info.status == "failed":
                    self.stats.total_failed += 1
                    self.process_history[pid].append((datetime.now(), "cleanup_failed"))
                    logger.error(f"Failed to clean up zombie process {pid} after {zombie_info.cleanup_attempts} attempts")
                else:
                    logger.warning(f"Cleanup attempt {zombie_info.cleanup_attempts} failed for zombie process {pid}, will retry")

            # Calculate success rate
            total_attempts = self.stats.total_cleaned + self.stats.total_failed
            if total_attempts > 0:
                self.stats.cleanup_success_rate = self.stats.total_cleaned / total_attempts

            return cleanup_successful

        except Exception as e:
            logger.error(f"Error during cleanup of zombie process {pid}: {e}")
            zombie_info.status = "failed"
            return False

    def _gentle_cleanup_zombie(self, pid: int, zombie_info: ZombieInfo) -> bool:
        """Attempt gentle cleanup of zombie process"""
        strategies = [
            ("wait_for_parent", self._wait_for_parent_reaping),
            ("signal_parent", self._signal_parent_to_reap),
            ("reap_by_init", self._reap_by_init_process)
        ]

        for strategy_name, strategy_func in strategies:
            try:
                logger.debug(f"Trying gentle cleanup strategy: {strategy_name} for PID {pid}")
                zombie_info.cleanup_method = strategy_name

                if strategy_func(pid, zombie_info):
                    return True

                time.sleep(self.config.cleanup_retry_delay)

            except Exception as e:
                logger.debug(f"Gentle cleanup strategy {strategy_name} failed: {e}")
                continue

        return False

    def _force_cleanup_zombie(self, pid: int, zombie_info: ZombieInfo) -> bool:
        """Attempt force cleanup of zombie process"""
        strategies = [
            ("kill_parent", self._kill_parent_process),
            ("system_reap", self._system_level_reap),
            ("force_reap", self._force_reap_process)
        ]

        for strategy_name, strategy_func in strategies:
            try:
                logger.debug(f"Trying force cleanup strategy: {strategy_name} for PID {pid}")
                zombie_info.cleanup_method = strategy_name

                if strategy_func(pid, zombie_info):
                    return True

                time.sleep(0.5)

            except Exception as e:
                logger.debug(f"Force cleanup strategy {strategy_name} failed: {e}")
                continue

        return False

    def _wait_for_parent_reaping(self, pid: int, zombie_info: ZombieInfo) -> bool:
        """Wait for parent process to reap the zombie"""
        try:
            # Check if parent is still alive and can reap
            try:
                parent_process = psutil.Process(zombie_info.ppid)
                if parent_process.is_running():
                    # Wait a short time for parent to reap
                    time.sleep(2.0)

                    # Check if zombie still exists
                    try:
                        psutil.Process(pid)
                        return False  # Still exists
                    except psutil.NoSuchProcess:
                        return True  # Reaped by parent
            except psutil.NoSuchProcess:
                # Parent is dead, zombie should be reaped by init
                pass

            return False

        except Exception:
            return False

    def _signal_parent_to_reap(self, pid: int, zombie_info: ZombieInfo) -> bool:
        """Signal parent process to reap zombie"""
        try:
            # Send SIGCHLD to parent to prompt reaping
            os.kill(zombie_info.ppid, signal.SIGCHLD)
            time.sleep(1.0)

            # Check if zombie was reaped
            try:
                psutil.Process(pid)
                return False
            except psutil.NoSuchProcess:
                return True

        except (ProcessLookupError, PermissionError):
            return False

    def _reap_by_init_process(self, pid: int, zombie_info: ZombieInfo) -> bool:
        """Attempt to have init process (PID 1) reap the zombie"""
        try:
            # On Unix systems, init will reap orphaned zombies
            # We can't directly signal init, but we can check if zombie gets reaped

            # Give the system time to reap
            time.sleep(3.0)

            try:
                psutil.Process(pid)
                return False
            except psutil.NoSuchProcess:
                return True

        except Exception:
            return False

    def _kill_parent_process(self, pid: int, zombie_info: ZombieInfo) -> bool:
        """Kill parent process to trigger zombie reaping by init"""
        try:
            parent_process = psutil.Process(zombie_info.ppid)
            if parent_process.is_running():
                parent_process.terminate()
                parent_process.wait(timeout=self.config.force_kill_timeout)

                # Check if zombie was reaped
                time.sleep(1.0)
                try:
                    psutil.Process(pid)
                    return False
                except psutil.NoSuchProcess:
                    return True

            return False

        except Exception:
            return False

    def _system_level_reap(self, pid: int, zombie_info: ZombieInfo) -> bool:
        """Use system-level tools to reap zombie"""
        try:
            # Try using the 'wait' command if available
            result = subprocess.run(
                ['wait', str(pid)],
                capture_output=True,
                timeout=self.config.force_kill_timeout
            )
            return result.returncode == 0

        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
            return False

    def _force_reap_process(self, pid: int, zombie_info: ZombieInfo) -> bool:
        """Final attempt to force reap the zombie"""
        try:
            # Try to send SIGKILL to the zombie process
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.5)

            # Check if process is gone
            try:
                psutil.Process(pid)
                return False
            except psutil.NoSuchProcess:
                return True

        except (ProcessLookupError, PermissionError):
            # Process might already be gone
            return True

    def _monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("Zombie detection monitoring loop started")

        while self.monitoring_active:
            try:
                self.scan_for_zombies()
                time.sleep(self.config.scan_interval)

            except Exception as e:
                logger.error(f"Error in zombie detection loop: {e}")
                time.sleep(self.config.scan_interval)

        logger.info("Zombie detection monitoring loop ended")

    def _cleanup_loop(self):
        """Cleanup loop for automatic zombie reaping"""
        logger.info("Zombie cleanup loop started")

        while self.monitoring_active:
            try:
                # Get zombies that need cleanup
                current_time = datetime.now()
                zombies_to_clean = []

                for pid, zombie_info in self.detected_zombies.items():
                    # Check if zombie needs cleanup based on age
                    zombie_age = (current_time - zombie_info.detection_time).total_seconds() / 60.0

                    if (zombie_age >= self.config.zombie_detection_threshold or
                        zombie_info.cleanup_attempts > 0):
                        zombies_to_clean.append(pid)

                # Clean up zombies
                for pid in zombies_to_clean:
                    zombie_info = self.detected_zombies.get(pid)
                    if zombie_info:
                        self.cleanup_zombie(pid)

                time.sleep(self.config.cleanup_retry_delay * 2)

            except Exception as e:
                logger.error(f"Error in zombie cleanup loop: {e}")
                time.sleep(self.config.cleanup_retry_delay * 2)

        logger.info("Zombie cleanup loop ended")

    def _find_worker_id(self, pid: int) -> Optional[int]:
        """Find worker ID associated with a process PID"""
        for worker_id, worker_pid in self.managed_processes.items():
            if worker_pid == pid:
                return worker_id
        return None

    def _get_process_affinity(self, pid: int) -> Optional[List[int]]:
        """Get CPU affinity for a process"""
        try:
            process = psutil.Process(pid)
            return process.cpu_affinity()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def _get_process_memory(self, pid: int) -> float:
        """Get memory usage for a process in MB"""
        try:
            process = psutil.Process(pid)
            return process.memory_info().rss / (1024 * 1024)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0

    def _check_alert_conditions(self):
        """Check if alerting conditions are met"""
        current_time = datetime.now()
        zombie_count = len(self.detected_zombies)

        # Check alert threshold
        if zombie_count >= self.config.alert_threshold_zombies:
            if not self.alert_cooldown_active:
                self._send_alert(f"High zombie process count: {zombie_count}")
                self.last_alert_time = current_time
                self.alert_cooldown_active = True

                # Start cooldown timer
                threading.Timer(
                    self.config.alert_cooldown_minutes * 60,
                    self._reset_alert_cooldown
                ).start()

    def _send_alert(self, message: str):
        """Send alert (placeholder for actual alerting mechanism)"""
        logger.warning(f"ZOMBIE ALERT: {message}")
        # In a real implementation, this could send to monitoring system,
        # email, Slack, etc.

    def _reset_alert_cooldown(self):
        """Reset alert cooldown"""
        self.alert_cooldown_active = False

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive detector statistics"""
        return {
            'detector_stats': {
                'monitoring_active': self.monitoring_active,
                'current_zombies': len(self.detected_zombies),
                'managed_processes': len(self.managed_processes)
            },
            'zombie_stats': {
                'total_detected': self.stats.total_detected,
                'total_cleaned': self.stats.total_cleaned,
                'total_failed': self.stats.total_failed,
                'current_active': self.stats.current_active_zombies,
                'peak_count': self.stats.peak_zombie_count,
                'cleanup_success_rate': self.stats.cleanup_success_rate,
                'detection_rate_per_minute': self.stats.detection_rate_per_minute,
                'average_cleanup_time': self.stats.average_cleanup_time,
                'last_detection': self.stats.last_detection.isoformat() if self.stats.last_detection else None,
                'last_cleanup': self.stats.last_cleanup.isoformat() if self.stats.last_cleanup else None
            },
            'active_zombies': [
                {
                    'pid': pid,
                    'ppid': info.ppid,
                    'worker_id': info.worker_id,
                    'process_name': info.process_name,
                    'detection_time': info.detection_time.isoformat(),
                    'cleanup_attempts': info.cleanup_attempts,
                    'status': info.status,
                    'age_minutes': (datetime.now() - info.detection_time).total_seconds() / 60.0
                }
                for pid, info in self.detected_zombies.items()
            ],
            'recent_activity': {
                'detections': [
                    {'timestamp': ts.isoformat(), 'count': count}
                    for ts, count in self.detection_history[-10:]
                ],
                'cleanups': [
                    {'timestamp': ts.isoformat(), 'duration': duration, 'success': success}
                    for ts, duration, success in self.cleanup_history[-10:]
                ]
            }
        }

    def force_cleanup_all_zombies(self) -> int:
        """
        Force cleanup of all detected zombies

        Returns:
            Number of zombies successfully cleaned
        """
        cleaned_count = 0
        zombie_pids = list(self.detected_zombies.keys())

        logger.info(f"Force cleaning {len(zombie_pids)} zombie processes")

        for pid in zombie_pids:
            if self.cleanup_zombie(pid, force=True):
                cleaned_count += 1

        logger.info(f"Force cleanup completed: {cleaned_count}/{len(zombie_pids)} zombies cleaned")
        return cleaned_count
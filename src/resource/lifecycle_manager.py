#!/usr/bin/env python3
"""
Process Lifecycle Manager
Multi-phase graceful shutdown with comprehensive signal handling
"""

import os
import sys
import time
import signal
import logging
import threading
import multiprocessing as mp
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import psutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


class ShutdownPhase(Enum):
    """Shutdown phases for coordinated graceful shutdown"""
    PREPARATION = 1
    GRACEFUL_STOP = 2
    FORCE_TERMINATION = 3
    CLEANUP_VALIDATION = 4


@dataclass
class LifecycleConfig:
    """Configuration for process lifecycle management"""
    # Phase timeouts (seconds)
    preparation_timeout: float = 5.0
    graceful_stop_timeout: float = 20.0
    force_termination_timeout: float = 5.0
    cleanup_validation_timeout: float = 3.0

    # Process monitoring
    health_check_interval: float = 1.0
    heartbeat_timeout: float = 10.0
    max_restart_attempts: int = 3

    # Signal handling
    enable_signal_handlers: bool = True
    custom_signal_handlers: Dict[int, Callable] = field(default_factory=dict)

    # Graceful shutdown settings
    enable_task_drain: bool = True
    enable_resource_cleanup: bool = True
    enable_cleanup_validation: bool = True

    # Recovery settings
    enable_auto_recovery: bool = True
    recovery_cooldown: float = 5.0


@dataclass
class ProcessInfo:
    """Information about a managed process"""
    pid: int
    worker_id: int
    process: mp.Process
    created_at: datetime
    last_heartbeat: datetime
    restart_count: int = 0
    is_critical: bool = False
    cleanup_handlers: List[Callable] = field(default_factory=list)
    status: str = "running"  # running, stopping, terminated, zombie
    shutdown_phase: Optional[ShutdownPhase] = None


@dataclass
class ShutdownMetrics:
    """Metrics for shutdown process"""
    start_time: datetime
    current_phase: ShutdownPhase
    processes_by_phase: Dict[ShutdownPhase, List[int]] = field(default_factory=dict)
    phase_start_times: Dict[ShutdownPhase, datetime] = field(default_factory=dict)
    completion_time: Optional[datetime] = None
    total_duration: Optional[float] = None
    success: bool = False


class ProcessLifecycleManager:
    """
    Advanced process lifecycle manager with multi-phase graceful shutdown

    Features:
    - 4-phase coordinated shutdown sequence
    - Configurable timeouts and phase coordination
    - Comprehensive signal handling (TERM, INT, USR1)
    - Process health monitoring and automatic recovery
    - Zombie process prevention and cleanup
    - Resource cleanup validation
    - Production-grade error handling and logging
    """

    def __init__(
        self,
        config: Optional[LifecycleConfig] = None,
        max_workers: int = 32
    ):
        self.config = config or LifecycleConfig()
        self.max_workers = max_workers

        # Process management
        self.managed_processes: Dict[int, ProcessInfo] = {}
        self.critical_processes: Set[int] = set()

        # Shutdown state
        self.is_shutting_down = False
        self.shutdown_metrics: Optional[ShutdownMetrics] = None
        self.shutdown_complete_event = threading.Event()

        # Signal handling
        self.original_signal_handlers: Dict[int, Callable] = {}
        self.signal_handlers_active = False

        # Monitoring
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.heartbeat_thread: Optional[threading.Thread] = None

        # Recovery
        self.recovery_active = False
        self.last_recovery_attempt: Dict[int, datetime] = {}

        # Statistics
        self.stats = {
            'total_processes_managed': 0,
            'successful_clean_shutdowns': 0,
            'forced_terminations': 0,
            'zombie_processes_detected': 0,
            'auto_recoveries': 0,
            'signal_interrupts_handled': 0
        }

        logger.info(f"ProcessLifecycleManager initialized for {max_workers} workers")
        logger.info(f"Shutdown timeouts - Preparation: {self.config.preparation_timeout}s, "
                   f"Graceful: {self.config.graceful_stop_timeout}s, "
                   f"Force: {self.config.force_termination_timeout}s")

    def register_process(
        self,
        process: mp.Process,
        worker_id: int,
        is_critical: bool = False,
        cleanup_handlers: Optional[List[Callable]] = None
    ) -> bool:
        """
        Register a process for lifecycle management

        Args:
            process: Multiprocessing process to manage
            worker_id: Worker identifier
            is_critical: Whether this process is critical for system operation
            cleanup_handlers: List of cleanup functions to call during shutdown

        Returns:
            True if registration successful
        """
        try:
            if worker_id in self.managed_processes:
                logger.warning(f"Worker {worker_id} already registered")
                return False

            process_info = ProcessInfo(
                pid=process.pid,
                worker_id=worker_id,
                process=process,
                created_at=datetime.now(),
                last_heartbeat=datetime.now(),
                is_critical=is_critical,
                cleanup_handlers=cleanup_handlers or []
            )

            self.managed_processes[worker_id] = process_info

            if is_critical:
                self.critical_processes.add(worker_id)

            self.stats['total_processes_managed'] += 1

            logger.info(f"Registered process {process.pid} for worker {worker_id} "
                       f"(critical: {is_critical})")
            return True

        except Exception as e:
            logger.error(f"Failed to register process for worker {worker_id}: {e}")
            return False

    def unregister_process(self, worker_id: int) -> bool:
        """
        Unregister a process from lifecycle management

        Args:
            worker_id: Worker identifier to unregister

        Returns:
            True if unregistration successful
        """
        try:
            if worker_id not in self.managed_processes:
                logger.warning(f"Worker {worker_id} not registered")
                return False

            process_info = self.managed_processes[worker_id]

            # Perform cleanup before unregistration
            if process_info.cleanup_handlers:
                self._execute_cleanup_handlers(process_info.cleanup_handlers, worker_id)

            # Remove from managed processes
            del self.managed_processes[worker_id]
            self.critical_processes.discard(worker_id)

            logger.info(f"Unregistered process for worker {worker_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to unregister process for worker {worker_id}: {e}")
            return False

    def start_monitoring(self):
        """Start process monitoring and signal handling"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return

        logger.info("Starting process lifecycle monitoring...")

        self.monitoring_active = True

        # Set up signal handlers
        if self.config.enable_signal_handlers:
            self._setup_signal_handlers()

        # Start monitoring threads
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            name="LifecycleMonitor",
            daemon=True
        )
        self.monitor_thread.start()

        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            name="HeartbeatMonitor",
            daemon=True
        )
        self.heartbeat_thread.start()

        logger.info("Process lifecycle monitoring started")

    def stop_monitoring(self):
        """Stop process monitoring and signal handling"""
        if not self.monitoring_active:
            return

        logger.info("Stopping process lifecycle monitoring...")

        self.monitoring_active = False

        # Restore original signal handlers
        if self.signal_handlers_active:
            self._restore_signal_handlers()

        # Wait for monitoring threads
        for thread in [self.monitor_thread, self.heartbeat_thread]:
            if thread and thread.is_alive():
                thread.join(timeout=2.0)

        logger.info("Process lifecycle monitoring stopped")

    def graceful_shutdown(self, timeout: Optional[float] = None) -> bool:
        """
        Execute multi-phase graceful shutdown

        Args:
            timeout: Maximum total time for shutdown (uses config if None)

        Returns:
            True if shutdown completed successfully
        """
        if self.is_shutting_down:
            logger.warning("Shutdown already in progress")
            return self.shutdown_complete_event.wait(timeout=timeout) if timeout else False

        if timeout is None:
            timeout = (
                self.config.preparation_timeout +
                self.config.graceful_stop_timeout +
                self.config.force_termination_timeout +
                self.config.cleanup_validation_timeout
            )

        logger.info(f"Starting graceful shutdown (timeout: {timeout}s)")
        self.is_shutting_down = True

        # Initialize shutdown metrics
        self.shutdown_metrics = ShutdownMetrics(
            start_time=datetime.now(),
            current_phase=ShutdownPhase.PREPARATION
        )

        try:
            # Phase 1: Preparation
            if not self._execute_phase_preparation():
                logger.error("Phase 1 (Preparation) failed")
                return False

            # Phase 2: Graceful Stop
            if not self._execute_phase_graceful_stop():
                logger.error("Phase 2 (Graceful Stop) failed")
                return False

            # Phase 3: Force Termination
            if not self._execute_phase_force_termination():
                logger.error("Phase 3 (Force Termination) failed")
                return False

            # Phase 4: Cleanup Validation
            if not self._execute_phase_cleanup_validation():
                logger.error("Phase 4 (Cleanup Validation) failed")
                return False

            # Shutdown completed successfully
            self.shutdown_metrics.completion_time = datetime.now()
            self.shutdown_metrics.total_duration = (
                self.shutdown_metrics.completion_time - self.shutdown_metrics.start_time
            ).total_seconds()
            self.shutdown_metrics.success = True

            self.stats['successful_clean_shutdowns'] += 1

            logger.info(f"Graceful shutdown completed in {self.shutdown_metrics.total_duration:.2f}s")
            self.shutdown_complete_event.set()
            return True

        except Exception as e:
            logger.error(f"Graceful shutdown failed: {e}")
            return False

        finally:
            self.is_shutting_down = False

    def emergency_shutdown(self) -> bool:
        """
        Emergency shutdown - terminate all processes immediately

        Returns:
            True if emergency shutdown completed
        """
        logger.warning("EMERGENCY SHUTDOWN INITIATED")

        success = True
        terminated_count = 0

        for worker_id, process_info in self.managed_processes.items():
            try:
                if process_info.process.is_alive():
                    logger.info(f"Emergency terminating worker {worker_id} (PID: {process_info.pid})")
                    process_info.process.terminate()
                    process_info.process.join(timeout=1.0)

                    if process_info.process.is_alive():
                        logger.warning(f"Force killing worker {worker_id} (PID: {process_info.pid})")
                        process_info.process.kill()
                        process_info.process.join(timeout=0.5)

                    terminated_count += 1

            except Exception as e:
                logger.error(f"Failed to emergency terminate worker {worker_id}: {e}")
                success = False

        logger.info(f"Emergency shutdown completed - terminated {terminated_count} processes")
        return success

    def _execute_phase_preparation(self) -> bool:
        """Execute Phase 1: Preparation"""
        logger.info("Phase 1: Preparation")

        self.shutdown_metrics.current_phase = ShutdownPhase.PREPARATION
        self.shutdown_metrics.phase_start_times[ShutdownPhase.PREPARATION] = datetime.now()
        self.shutdown_metrics.processes_by_phase[ShutdownPhase.PREPARATION] = list(self.managed_processes.keys())

        try:
            # Notify all processes about impending shutdown
            for worker_id, process_info in self.managed_processes.items():
                process_info.shutdown_phase = ShutdownPhase.PREPARATION
                process_info.status = "stopping"

                # Send preparation signal if process supports it
                if hasattr(process_info.process, 'send_signal'):
                    try:
                        os.kill(process_info.pid, signal.SIGUSR1)
                    except (ProcessLookupError, PermissionError):
                        pass  # Process may already be dead

            # Wait for preparation timeout
            start_time = time.time()
            while time.time() - start_time < self.config.preparation_timeout:
                if self._check_all_processes_ready_for_phase(ShutdownPhase.GRACEFUL_STOP):
                    break
                time.sleep(0.1)

            phase_duration = (datetime.now() -
                            self.shutdown_metrics.phase_start_times[ShutdownPhase.PREPARATION]).total_seconds()
            logger.info(f"Phase 1 completed in {phase_duration:.2f}s")
            return True

        except Exception as e:
            logger.error(f"Phase 1 failed: {e}")
            return False

    def _execute_phase_graceful_stop(self) -> bool:
        """Execute Phase 2: Graceful Stop"""
        logger.info("Phase 2: Graceful Stop")

        self.shutdown_metrics.current_phase = ShutdownPhase.GRACEFUL_STOP
        self.shutdown_metrics.phase_start_times[ShutdownPhase.GRACEFUL_STOP] = datetime.now()
        self.shutdown_metrics.processes_by_phase[ShutdownPhase.GRACEFUL_STOP] = [
            worker_id for worker_id, process_info in self.managed_processes.items()
            if process_info.process.is_alive()
        ]

        try:
            # Execute cleanup handlers for each process
            for worker_id, process_info in self.managed_processes.items():
                if process_info.process.is_alive():
                    process_info.shutdown_phase = ShutdownPhase.GRACEFUL_STOP

                    # Execute cleanup handlers
                    if process_info.cleanup_handlers:
                        self._execute_cleanup_handlers(process_info.cleanup_handlers, worker_id)

            # Wait for graceful shutdown timeout
            start_time = time.time()
            alive_processes = set()

            while time.time() - start_time < self.config.graceful_stop_timeout:
                alive_processes = {
                    worker_id for worker_id, process_info in self.managed_processes.items()
                    if process_info.process.is_alive()
                }

                if not alive_processes:
                    break

                time.sleep(0.1)

            # Terminate remaining processes
            for worker_id in alive_processes:
                process_info = self.managed_processes[worker_id]
                logger.info(f"Terminating worker {worker_id} (PID: {process_info.pid})")
                process_info.process.terminate()

            # Wait for termination
            time.sleep(1.0)

            phase_duration = (datetime.now() -
                            self.shutdown_metrics.phase_start_times[ShutdownPhase.GRACEFUL_STOP]).total_seconds()
            logger.info(f"Phase 2 completed in {phase_duration:.2f}s")
            return True

        except Exception as e:
            logger.error(f"Phase 2 failed: {e}")
            return False

    def _execute_phase_force_termination(self) -> bool:
        """Execute Phase 3: Force Termination"""
        logger.info("Phase 3: Force Termination")

        self.shutdown_metrics.current_phase = ShutdownPhase.FORCE_TERMINATION
        self.shutdown_metrics.phase_start_times[ShutdownPhase.FORCE_TERMINATION] = datetime.now()
        self.shutdown_metrics.processes_by_phase[ShutdownPhase.FORCE_TERMINATION] = [
            worker_id for worker_id, process_info in self.managed_processes.items()
            if process_info.process.is_alive()
        ]

        try:
            terminated_count = 0

            for worker_id, process_info in self.managed_processes.items():
                if process_info.process.is_alive():
                    process_info.shutdown_phase = ShutdownPhase.FORCE_TERMINATION
                    process_info.status = "terminated"

                    logger.warning(f"Force killing worker {worker_id} (PID: {process_info.pid})")
                    process_info.process.kill()
                    process_info.process.join(timeout=0.5)
                    terminated_count += 1
                    self.stats['forced_terminations'] += 1

            phase_duration = (datetime.now() -
                            self.shutdown_metrics.phase_start_times[ShutdownPhase.FORCE_TERMINATION]).total_seconds()
            logger.info(f"Phase 3 completed in {phase_duration:.2f}s - force terminated {terminated_count} processes")
            return True

        except Exception as e:
            logger.error(f"Phase 3 failed: {e}")
            return False

    def _execute_phase_cleanup_validation(self) -> bool:
        """Execute Phase 4: Cleanup Validation"""
        logger.info("Phase 4: Cleanup Validation")

        self.shutdown_metrics.current_phase = ShutdownPhase.CLEANUP_VALIDATION
        self.shutdown_metrics.phase_start_times[ShutdownPhase.CLEANUP_VALIDATION] = datetime.now()

        try:
            # Validate all processes are terminated
            zombie_processes = []
            for worker_id, process_info in self.managed_processes.items():
                if process_info.process.is_alive():
                    zombie_processes.append(worker_id)
                    self.stats['zombie_processes_detected'] += 1

                # Update final status
                process_info.status = "terminated" if worker_id not in zombie_processes else "zombie"

            if zombie_processes:
                logger.error(f"Detected {len(zombie_processes)} zombie processes: {zombie_processes}")
                # Force kill any remaining zombie processes
                for worker_id in zombie_processes:
                    try:
                        process_info = self.managed_processes[worker_id]
                        os.kill(process_info.pid, signal.SIGKILL)
                    except (ProcessLookupError, PermissionError):
                        pass  # Process already dead or permission denied

            # Cleanup managed processes dictionary
            self.managed_processes.clear()
            self.critical_processes.clear()

            phase_duration = (datetime.now() -
                            self.shutdown_metrics.phase_start_times[ShutdownPhase.CLEANUP_VALIDATION]).total_seconds()
            logger.info(f"Phase 4 completed in {phase_duration:.2f}s")
            return True

        except Exception as e:
            logger.error(f"Phase 4 failed: {e}")
            return False

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            self.stats['signal_interrupts_handled'] += 1

            if signum in [signal.SIGTERM, signal.SIGINT]:
                # Initiate graceful shutdown
                threading.Thread(
                    target=self.graceful_shutdown,
                    name="SignalShutdown",
                    daemon=True
                ).start()
            elif signum == signal.SIGUSR1:
                # Custom signal handler
                if signum in self.config.custom_signal_handlers:
                    self.config.custom_signal_handlers[signum]()

        # Register signal handlers
        signals_to_handle = [signal.SIGTERM, signal.SIGINT, signal.SIGUSR1]

        for sig in signals_to_handle:
            try:
                # Store original handler
                self.original_signal_handlers[sig] = signal.signal(sig, signal_handler)
                self.signal_handlers_active = True
                logger.debug(f"Registered signal handler for {sig}")
            except (OSError, ValueError) as e:
                logger.warning(f"Failed to register signal handler for {sig}: {e}")

    def _restore_signal_handlers(self):
        """Restore original signal handlers"""
        for sig, handler in self.original_signal_handlers.items():
            try:
                signal.signal(sig, handler)
                logger.debug(f"Restored signal handler for {sig}")
            except (OSError, ValueError) as e:
                logger.warning(f"Failed to restore signal handler for {sig}: {e}")

        self.signal_handlers_active = False

    def _monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("Lifecycle monitoring loop started")

        while self.monitoring_active:
            try:
                # Check process health
                self._check_process_health()

                # Perform auto-recovery if enabled
                if self.config.enable_auto_recovery and not self.recovery_active:
                    self._perform_auto_recovery()

                time.sleep(self.config.health_check_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.config.health_check_interval)

        logger.info("Lifecycle monitoring loop ended")

    def _heartbeat_loop(self):
        """Heartbeat monitoring loop"""
        logger.info("Heartbeat monitoring loop started")

        while self.monitoring_active:
            try:
                current_time = datetime.now()
                timeout_processes = []

                for worker_id, process_info in self.managed_processes.items():
                    if (current_time - process_info.last_heartbeat).total_seconds() > self.config.heartbeat_timeout:
                        timeout_processes.append(worker_id)

                # Handle timeout processes
                for worker_id in timeout_processes:
                    logger.warning(f"Worker {worker_id} heartbeat timeout")
                    if self.config.enable_auto_recovery:
                        self._schedule_recovery(worker_id)

                time.sleep(self.config.health_check_interval)

            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                time.sleep(self.config.health_check_interval)

        logger.info("Heartbeat monitoring loop ended")

    def _check_process_health(self):
        """Check health of managed processes"""
        for worker_id, process_info in self.managed_processes.items():
            try:
                if not process_info.process.is_alive():
                    if process_info.status == "running":
                        logger.warning(f"Worker {worker_id} died unexpectedly")
                        process_info.status = "terminated"

                        if self.config.enable_auto_recovery:
                            self._schedule_recovery(worker_id)
                else:
                    # Update heartbeat for alive processes
                    process_info.last_heartbeat = datetime.now()

            except Exception as e:
                logger.error(f"Error checking health of worker {worker_id}: {e}")

    def _perform_auto_recovery(self):
        """Perform automatic recovery of failed processes"""
        if not self.config.enable_auto_recovery:
            return

        current_time = datetime.now()
        recovery_needed = []

        for worker_id in list(self.last_recovery_attempt.keys()):
            if (current_time - self.last_recovery_attempt[worker_id]).total_seconds() > self.config.recovery_cooldown:
                recovery_needed.append(worker_id)
                del self.last_recovery_attempt[worker_id]

        for worker_id in recovery_needed:
            process_info = self.managed_processes.get(worker_id)
            if process_info and process_info.restart_count < self.config.max_restart_attempts:
                logger.info(f"Attempting recovery of worker {worker_id}")
                self.stats['auto_recoveries'] += 1
                # In a real implementation, this would restart the process
                # For now, just update the restart count
                process_info.restart_count += 1
                process_info.last_heartbeat = datetime.now()

    def _schedule_recovery(self, worker_id: int):
        """Schedule recovery for a failed process"""
        self.last_recovery_attempt[worker_id] = datetime.now()

    def _execute_cleanup_handlers(self, handlers: List[Callable], worker_id: int):
        """Execute cleanup handlers for a process"""
        for i, handler in enumerate(handlers):
            try:
                logger.debug(f"Executing cleanup handler {i+1}/{len(handlers)} for worker {worker_id}")
                handler(worker_id)
            except Exception as e:
                logger.error(f"Cleanup handler {i+1} failed for worker {worker_id}: {e}")

    def _check_all_processes_ready_for_phase(self, next_phase: ShutdownPhase) -> bool:
        """Check if all processes are ready for the next shutdown phase"""
        # In a real implementation, this would check if processes have acknowledged
        # their readiness for the next phase. For now, return True after a short delay.
        return time.time() > (self.shutdown_metrics.phase_start_times[self.shutdown_metrics.current_phase].timestamp() +
                             self.config.preparation_timeout / 2)

    def update_heartbeat(self, worker_id: int):
        """Update heartbeat for a specific worker"""
        if worker_id in self.managed_processes:
            self.managed_processes[worker_id].last_heartbeat = datetime.now()

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the lifecycle manager"""
        return {
            'monitoring_active': self.monitoring_active,
            'is_shutting_down': self.is_shutting_down,
            'managed_processes': len(self.managed_processes),
            'critical_processes': len(self.critical_processes),
            'current_shutdown_phase': self.shutdown_metrics.current_phase.value if self.shutdown_metrics else None,
            'shutdown_complete': self.shutdown_complete_event.is_set(),
            'stats': self.stats.copy(),
            'process_details': {
                worker_id: {
                    'pid': info.pid,
                    'status': info.status,
                    'restart_count': info.restart_count,
                    'last_heartbeat': info.last_heartbeat.isoformat(),
                    'uptime_seconds': (datetime.now() - info.created_at).total_seconds()
                }
                for worker_id, info in self.managed_processes.items()
            }
        }

    def get_shutdown_metrics(self) -> Optional[Dict[str, Any]]:
        """Get shutdown metrics if shutdown was performed"""
        if not self.shutdown_metrics:
            return None

        return {
            'start_time': self.shutdown_metrics.start_time.isoformat(),
            'completion_time': self.shutdown_metrics.completion_time.isoformat() if self.shutdown_metrics.completion_time else None,
            'total_duration': self.shutdown_metrics.total_duration,
            'success': self.shutdown_metrics.success,
            'phases': {
                phase.value: {
                    'duration': (
                        self.shutdown_metrics.phase_start_times.get(phase, datetime.now()) -
                        self.shutdown_metrics.phase_start_times.get(phase, datetime.now())
                    ).total_seconds() if phase in self.shutdown_metrics.phase_start_times else 0,
                    'process_count': len(self.shutdown_metrics.processes_by_phase.get(phase, []))
                }
                for phase in ShutdownPhase
            }
        }
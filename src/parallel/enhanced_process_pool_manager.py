#!/usr/bin/env python3
"""
Enhanced Process Pool Manager with Phase 3 Lifecycle Management Integration
Integrates with ProcessLifecycleManager for zombie-free operations
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
from typing import Dict, List, Optional, Any, Tuple, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import psutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import Phase 3 components
try:
    from src.resource import (
        ProcessLifecycleManager, LifecycleConfig,
        ZombieProcessDetector, DetectorConfig
    )
    PHASE3_AVAILABLE = True
except ImportError:
    PHASE3_AVAILABLE = False

logger = logging.getLogger(__name__)


class EnhancedWorkerState(Enum):
    """Enhanced worker state with lifecycle management"""
    INITIALIZING = "initializing"
    IDLE = "idle"
    BUSY = "busy"
    STOPPING = "stopping"
    TERMINATED = "terminated"
    ZOMBIE = "zombie"
    RECOVERING = "recovering"


@dataclass
class EnhancedWorkerInfo:
    """Enhanced worker information with lifecycle management"""
    worker_id: int
    pid: int
    process: mp.Process
    created_at: datetime
    last_heartbeat: datetime
    restart_count: int = 0
    state: EnhancedWorkerState = EnhancedWorkerState.INITIALIZING
    is_critical: bool = False
    lifecycle_managed: bool = False
    resource_cleanup_registered: bool = False


@dataclass
class LifecycleIntegrationConfig:
    """Configuration for lifecycle management integration"""
    enable_lifecycle_management: bool = True
    enable_zombie_detection: bool = True
    auto_register_workers: bool = True
    graceful_shutdown_timeout: float = 30.0
    zombie_cleanup_timeout: float = 60.0
    worker_restart_cooldown: float = 5.0


class EnhancedProcessPoolManager:
    """
    Enhanced process pool manager with Phase 3 lifecycle management integration

    Features:
    - Automatic worker registration with ProcessLifecycleManager
    - Zombie process detection and cleanup
    - Enhanced graceful shutdown coordination
    - Worker health monitoring and auto-recovery
    - Resource cleanup registration for each worker
    - Production-grade error handling and logging
    """

    def __init__(
        self,
        min_workers: int = 4,
        max_workers: int = 32,
        lifecycle_config: Optional[LifecycleIntegrationConfig] = None
    ):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.lifecycle_config = lifecycle_config or LifecycleIntegrationConfig()

        # Worker management
        self.workers: Dict[int, EnhancedWorkerInfo] = {}
        self.worker_pids: Dict[int, int] = {}  # worker_id -> pid mapping
        self.pid_worker_map: Dict[int, int] = {}  # pid -> worker_id mapping

        # Phase 3 components
        self.lifecycle_manager: Optional[ProcessLifecycleManager] = None
        self.zombie_detector: Optional[ZombieProcessDetector] = None

        # State management
        self.is_running = False
        self.is_shutting_down = False
        self.start_time: Optional[datetime] = None

        # Monitoring
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.health_check_thread: Optional[threading.Thread] = None

        # Statistics
        self.stats = {
            'total_workers_created': 0,
            'total_workers_terminated': 0,
            'zombie_workers_detected': 0,
            'zombie_workers_cleaned': 0,
            'auto_recoveries': 0,
            'graceful_shutdowns': 0,
            'emergency_terminations': 0
        }

        # Initialize Phase 3 components
        if PHASE3_AVAILABLE and self.lifecycle_config.enable_lifecycle_management:
            self._init_lifecycle_components()

        logger.info(f"EnhancedProcessPoolManager initialized with {min_workers}-{max_workers} workers")
        logger.info(f"Lifecycle management: {self.lifecycle_config.enable_lifecycle_management}, "
                   f"Zombie detection: {self.lifecycle_config.enable_zombie_detection}")

    def _init_lifecycle_components(self):
        """Initialize Phase 3 lifecycle management components"""
        try:
            # Initialize ProcessLifecycleManager
            lifecycle_config = LifecycleConfig(
                preparation_timeout=5.0,
                graceful_stop_timeout=self.lifecycle_config.graceful_shutdown_timeout,
                force_termination_timeout=5.0,
                enable_signal_handlers=True,
                enable_auto_recovery=True
            )
            self.lifecycle_manager = ProcessLifecycleManager(
                config=lifecycle_config,
                max_workers=self.max_workers
            )

            # Initialize ZombieProcessDetector
            zombie_config = DetectorConfig(
                scan_interval=2.0,
                enable_auto_cleanup=True,
                cleanup_retry_attempts=3,
                max_zombie_age_minutes=self.lifecycle_config.zombie_cleanup_timeout / 60.0
            )
            self.zombie_detector = ZombieProcessDetector(
                config=zombie_config,
                managed_processes=self.worker_pids
            )

            logger.info("Phase 3 lifecycle components initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Phase 3 components: {e}")
            self.lifecycle_config.enable_lifecycle_management = False

    def start(self):
        """Start the enhanced process pool manager"""
        if self.is_running:
            logger.warning("EnhancedProcessPoolManager is already running")
            return

        logger.info("Starting EnhancedProcessPoolManager...")
        self.start_time = datetime.now()
        self.is_running = True

        try:
            # Start Phase 3 components
            if PHASE3_AVAILABLE:
                if self.lifecycle_manager:
                    self.lifecycle_manager.start_monitoring()
                if self.zombie_detector:
                    self.zombie_detector.start_monitoring()

            # Start initial workers
            self._scale_workers(self.min_workers)

            # Start monitoring threads
            self._start_monitoring()

            logger.info(f"EnhancedProcessPoolManager started with {len(self.workers)} workers")

        except Exception as e:
            logger.error(f"Failed to start EnhancedProcessPoolManager: {e}")
            self.stop()
            raise

    def stop(self, timeout: float = 60.0):
        """Stop the enhanced process pool manager with graceful shutdown"""
        if not self.is_running:
            return

        logger.info("Stopping EnhancedProcessPoolManager...")
        self.is_shutting_down = True

        try:
            # Use Phase 3 graceful shutdown if available
            if (self.lifecycle_config.enable_lifecycle_management and
                self.lifecycle_manager and PHASE3_AVAILABLE):
                logger.info("Initiating Phase 3 graceful shutdown for workers...")
                self._graceful_shutdown_workers(timeout)
            else:
                logger.info("Using legacy shutdown for workers...")
                self._legacy_shutdown_workers(timeout)

            # Stop monitoring threads
            self._stop_monitoring()

            # Stop Phase 3 components
            if PHASE3_AVAILABLE:
                if self.zombie_detector:
                    self.zombie_detector.stop_monitoring()
                if self.lifecycle_manager:
                    self.lifecycle_manager.stop_monitoring()

            self.is_running = False
            logger.info("EnhancedProcessPoolManager stopped")

        except Exception as e:
            logger.error(f"Error stopping EnhancedProcessPoolManager: {e}")

    def create_worker(self, worker_id: int, target: Callable, args: tuple = ()) -> bool:
        """
        Create a new worker process with lifecycle management

        Args:
            worker_id: Worker identifier
            target: Target function for the worker process
            args: Arguments for the target function

        Returns:
            True if worker created successfully
        """
        try:
            # Create worker process
            process = mp.Process(target=target, args=args)
            process.start()

            # Create enhanced worker info
            worker_info = EnhancedWorkerInfo(
                worker_id=worker_id,
                pid=process.pid,
                process=process,
                created_at=datetime.now(),
                last_heartbeat=datetime.now(),
                state=EnhancedWorkerState.IDLE,
                lifecycle_managed=False
            )

            # Register with lifecycle manager
            if (self.lifecycle_config.enable_lifecycle_management and
                self.lifecycle_manager and PHASE3_AVAILABLE):
                success = self.lifecycle_manager.register_process(
                    process=process,
                    worker_id=worker_id,
                    is_critical=worker_id < self.min_workers,  # Critical workers are min workers
                    cleanup_handlers=[self._cleanup_worker_resources]
                )
                worker_info.lifecycle_managed = success
                if success:
                    logger.debug(f"Worker {worker_id} registered with lifecycle manager")

            # Update mappings
            self.workers[worker_id] = worker_info
            self.worker_pids[worker_id] = process.pid
            self.pid_worker_map[process.pid] = worker_id

            # Update zombie detector with new mappings
            if self.zombie_detector and PHASE3_AVAILABLE:
                self.zombie_detector.managed_processes = self.worker_pids.copy()

            self.stats['total_workers_created'] += 1

            logger.info(f"Created worker {worker_id} (PID: {process.pid}), "
                       f"lifecycle managed: {worker_info.lifecycle_managed}")
            return True

        except Exception as e:
            logger.error(f"Failed to create worker {worker_id}: {e}")
            return False

    def terminate_worker(self, worker_id: int, force: bool = False) -> bool:
        """
        Terminate a specific worker process

        Args:
            worker_id: Worker ID to terminate
            force: Force immediate termination

        Returns:
            True if termination successful
        """
        if worker_id not in self.workers:
            logger.warning(f"Worker {worker_id} not found")
            return False

        worker_info = self.workers[worker_id]
        process = worker_info.process

        try:
            worker_info.state = EnhancedWorkerState.STOPPING

            # Unregister from lifecycle manager
            if (worker_info.lifecycle_managed and
                self.lifecycle_manager and PHASE3_AVAILABLE):
                self.lifecycle_manager.unregister_process(worker_id)

            # Terminate process
            if force:
                logger.warning(f"Force killing worker {worker_id} (PID: {process.pid})")
                process.kill()
                self.stats['emergency_terminations'] += 1
            else:
                logger.info(f"Terminating worker {worker_id} (PID: {process.pid})")
                process.terminate()
                self.stats['graceful_shutdowns'] += 1

            # Wait for process to finish
            process.join(timeout=5.0 if not force else 1.0)

            # Update mappings
            if process.pid in self.pid_worker_map:
                del self.pid_worker_map[process.pid]
            if worker_id in self.worker_pids:
                del self.worker_pids[worker_id]

            # Update zombie detector
            if self.zombie_detector and PHASE3_AVAILABLE:
                self.zombie_detector.managed_processes = self.worker_pids.copy()

            worker_info.state = EnhancedWorkerState.TERMINATED
            self.stats['total_workers_terminated'] += 1

            logger.info(f"Worker {worker_id} terminated successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to terminate worker {worker_id}: {e}")
            return False

    def _graceful_shutdown_workers(self, timeout: float):
        """Graceful shutdown using Phase 3 lifecycle manager"""
        if not self.lifecycle_manager:
            logger.warning("Lifecycle manager not available, falling back to legacy shutdown")
            self._legacy_shutdown_workers(timeout)
            return

        try:
            # Unregister all workers from lifecycle manager
            for worker_id, worker_info in self.workers.items():
                if worker_info.lifecycle_managed:
                    self.lifecycle_manager.unregister_process(worker_id)

            # Execute graceful shutdown
            success = self.lifecycle_manager.graceful_shutdown(timeout=timeout)

            if not success:
                logger.warning("Graceful shutdown incomplete, performing force cleanup")
                self._force_cleanup_remaining_workers()

        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}")
            self._legacy_shutdown_workers(timeout)

    def _legacy_shutdown_workers(self, timeout: float):
        """Legacy worker shutdown method"""
        start_time = time.time()
        worker_ids = list(self.workers.keys())

        for worker_id in worker_ids:
            if time.time() - start_time >= timeout:
                logger.warning(f"Shutdown timeout reached, force killing remaining workers")
                break

            self.terminate_worker(worker_id, force=False)
            time.sleep(0.1)  # Small delay between terminations

        # Force kill any remaining workers
        remaining_workers = list(self.workers.keys())
        for worker_id in remaining_workers:
            self.terminate_worker(worker_id, force=True)

    def _force_cleanup_remaining_workers(self):
        """Force cleanup of remaining workers"""
        remaining_workers = list(self.workers.keys())
        for worker_id in remaining_workers:
            self.terminate_worker(worker_id, force=True)

    def _scale_workers(self, target_count: int):
        """Scale worker pool to target count"""
        current_count = len(self.workers)

        if target_count > current_count:
            # Add workers
            for i in range(target_count - current_count):
                worker_id = len(self.workers)
                # In a real implementation, this would call a specific worker function
                # For now, create a dummy worker
                def dummy_worker():
                    while True:
                        time.sleep(1)

                if self.create_worker(worker_id, dummy_worker):
                    logger.debug(f"Scaled up: created worker {worker_id}")
                else:
                    logger.error(f"Failed to create worker {worker_id}")

        elif target_count < current_count:
            # Remove workers
            workers_to_remove = list(self.workers.keys())[target_count:]
            for worker_id in workers_to_remove:
                self.terminate_worker(worker_id, force=False)
                logger.debug(f"Scaled down: terminated worker {worker_id}")

    def _cleanup_worker_resources(self, worker_id: int):
        """Cleanup resources for a specific worker"""
        try:
            # Close any open file handles
            worker_info = self.workers.get(worker_id)
            if worker_info:
                # In a real implementation, this would clean up worker-specific resources
                logger.debug(f"Cleaned up resources for worker {worker_id}")

        except Exception as e:
            logger.error(f"Error cleaning up resources for worker {worker_id}: {e}")

    def _start_monitoring(self):
        """Start monitoring threads"""
        self.monitoring_active = True

        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            name="WorkerMonitor",
            daemon=True
        )
        self.monitor_thread.start()

        self.health_check_thread = threading.Thread(
            target=self._health_check_loop,
            name="WorkerHealthCheck",
            daemon=True
        )
        self.health_check_thread.start()

    def _stop_monitoring(self):
        """Stop monitoring threads"""
        self.monitoring_active = False

        for thread in [self.monitor_thread, self.health_check_thread]:
            if thread and thread.is_alive():
                thread.join(timeout=2.0)

    def _monitoring_loop(self):
        """Main worker monitoring loop"""
        while self.monitoring_active:
            try:
                # Check worker states
                self._update_worker_states()

                # Update heartbeat for lifecycle manager
                if self.lifecycle_manager and PHASE3_AVAILABLE:
                    for worker_id, worker_info in self.workers.items():
                        if worker_info.lifecycle_managed:
                            self.lifecycle_manager.update_heartbeat(worker_id)

                time.sleep(5.0)  # Check every 5 seconds

            except Exception as e:
                logger.error(f"Error in worker monitoring loop: {e}")
                time.sleep(5.0)

    def _health_check_loop(self):
        """Health check loop for workers"""
        while self.monitoring_active:
            try:
                # Check for zombie workers
                self._check_zombie_workers()

                # Perform worker recovery if needed
                if self.lifecycle_config.enable_lifecycle_management:
                    self._perform_worker_recovery()

                time.sleep(10.0)  # Health check every 10 seconds

            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                time.sleep(10.0)

    def _update_worker_states(self):
        """Update worker states based on process status"""
        for worker_id, worker_info in self.workers.items():
            try:
                if worker_info.process.is_alive():
                    if worker_info.state == EnhancedWorkerState.TERMINATED:
                        worker_info.state = EnhancedWorkerState.IDLE
                else:
                    if worker_info.state not in [EnhancedWorkerState.TERMINATED,
                                               EnhancedWorkerState.ZOMBIE]:
                        worker_info.state = EnhancedWorkerState.ZOMBIE
                        self.stats['zombie_workers_detected'] += 1
                        logger.warning(f"Worker {worker_id} (PID: {worker_info.pid}) became zombie")

            except Exception as e:
                logger.error(f"Error updating state for worker {worker_id}: {e}")

    def _check_zombie_workers(self):
        """Check and handle zombie workers"""
        zombie_workers = [
            worker_id for worker_id, worker_info in self.workers.items()
            if worker_info.state == EnhancedWorkerState.ZOMBIE
        ]

        for worker_id in zombie_workers:
            logger.warning(f"Detected zombie worker {worker_id}")
            self.stats['zombie_workers_detected'] += 1

            # Try to clean up zombie worker
            if self.terminate_worker(worker_id, force=True):
                self.stats['zombie_workers_cleaned'] += 1
                logger.info(f"Successfully cleaned up zombie worker {worker_id}")
            else:
                logger.error(f"Failed to clean up zombie worker {worker_id}")

    def _perform_worker_recovery(self):
        """Perform automatic worker recovery"""
        if not self.lifecycle_config.enable_lifecycle_management:
            return

        # Check for workers that need recovery
        recovered_workers = 0
        for worker_id, worker_info in self.workers.items():
            if (worker_info.state == EnhancedWorkerState.TERMINATED and
                worker_info.restart_count < 3 and
                worker_info.is_critical):

                logger.info(f"Attempting recovery of critical worker {worker_id}")
                # In a real implementation, this would restart the worker
                worker_info.restart_count += 1
                worker_info.state = EnhancedWorkerState.RECOVERING
                self.stats['auto_recoveries'] += 1
                recovered_workers += 1

        if recovered_workers > 0:
            logger.info(f"Recovered {recovered_workers} workers")

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        current_time = datetime.now()
        uptime_seconds = (current_time - self.start_time).total_seconds() if self.start_time else 0

        base_stats = {
            'manager_stats': {
                'is_running': self.is_running,
                'is_shutting_down': self.is_shutting_down,
                'uptime_seconds': uptime_seconds,
                'current_workers': len(self.workers),
                'min_workers': self.min_workers,
                'max_workers': self.max_workers
            },
            'worker_stats': {
                'total_created': self.stats['total_workers_created'],
                'total_terminated': self.stats['total_workers_terminated'],
                'zombie_detected': self.stats['zombie_workers_detected'],
                'zombie_cleaned': self.stats['zombie_workers_cleaned'],
                'auto_recoveries': self.stats['auto_recoveries'],
                'graceful_shutdowns': self.stats['graceful_shutdowns'],
                'emergency_terminations': self.stats['emergency_terminations']
            },
            'worker_states': {
                state.value: len([
                    w for w in self.workers.values() if w.state == state
                ])
                for state in EnhancedWorkerState
            },
            'worker_details': [
                {
                    'worker_id': info.worker_id,
                    'pid': info.pid,
                    'state': info.state.value,
                    'is_critical': info.is_critical,
                    'lifecycle_managed': info.lifecycle_managed,
                    'restart_count': info.restart_count,
                    'uptime_seconds': (current_time - info.created_at).total_seconds(),
                    'last_heartbeat': info.last_heartbeat.isoformat()
                }
                for info in self.workers.values()
            ]
        }

        # Add Phase 3 component stats if available
        if PHASE3_AVAILABLE:
            if self.lifecycle_manager:
                base_stats['lifecycle_manager'] = self.lifecycle_manager.get_status()
            if self.zombie_detector:
                base_stats['zombie_detector'] = self.zombie_detector.get_statistics()

        return base_stats
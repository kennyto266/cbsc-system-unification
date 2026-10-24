#!/usr/bin/env python3
"""
Parallel Processing System for 32-Core CPU Backtesting
Enhanced with IPC Synchronization components (Phase 2)
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Feature flags for safe deployment
ENABLE_ATOMIC_INITIALIZER = os.getenv('ENABLE_ATOMIC_INITIALIZER', 'true').lower() == 'true'
ENABLE_DEADLOCK_DETECTION = os.getenv('ENABLE_DEADLOCK_DETECTION', 'true').lower() == 'true'
ENABLE_SMART_QUEUING = os.getenv('ENABLE_SMART_QUEUING', 'true').lower() == 'true'
ENABLE_IPC_ENHANCEMENTS = os.getenv('ENABLE_IPC_ENHANCEMENTS', 'true').lower() == 'true'

# Phase 3: Resource Lifecycle Management feature flags
ENABLE_LIFECYCLE_MANAGER = os.getenv('ENABLE_LIFECYCLE_MANAGER', 'true').lower() == 'true'
ENABLE_ZOMBIE_DETECTOR = os.getenv('ENABLE_ZOMBIE_DETECTOR', 'true').lower() == 'true'
ENABLE_RESOURCE_CLEANER = os.getenv('ENABLE_RESOURCE_CLEANER', 'true').lower() == 'true'
ENABLE_GRACEFUL_SHUTDOWN = os.getenv('ENABLE_GRACEFUL_SHUTDOWN', 'true').lower() == 'true'

# Import new IPC synchronization components
if ENABLE_IPC_ENHANCEMENTS:
    try:
        from src.ipc import (
            AtomicInitializer, InitializationPhase,
            DeadlockDetector, ResourceType, DeadlockResolution,
            SmartMessageQueue, MessagePriority, QueuePolicy
        )
        IPC_ENHANCEMENTS_AVAILABLE = True
    except ImportError as e:
        logger.warning(f"IPC enhancements not available: {e}")
        IPC_ENHANCEMENTS_AVAILABLE = False
else:
    IPC_ENHANCEMENTS_AVAILABLE = False

# Import Phase 3: Resource Lifecycle Management components
LIFECYCLE_MANAGEMENT_AVAILABLE = False
ZOMBIE_DETECTION_AVAILABLE = False
RESOURCE_CLEANING_AVAILABLE = False

if ENABLE_LIFECYCLE_MANAGER or ENABLE_ZOMBIE_DETECTOR or ENABLE_RESOURCE_CLEANER:
    try:
        from src.resource import (
            ProcessLifecycleManager, ShutdownPhase, LifecycleConfig,
            ZombieProcessDetector, ZombieStats, DetectorConfig,
            ResourceCleaner, ResourceType, CleanupHandler, CleanerConfig
        )
        LIFECYCLE_MANAGEMENT_AVAILABLE = True

        # Individual component availability
        if ENABLE_LIFECYCLE_MANAGER:
            ZOMBIE_DETECTION_AVAILABLE = True
        if ENABLE_ZOMBIE_DETECTOR:
            ZOMBIE_DETECTION_AVAILABLE = True
        if ENABLE_RESOURCE_CLEANER:
            RESOURCE_CLEANING_AVAILABLE = True

        logger.info("Phase 3 Resource Lifecycle Management components loaded successfully")
    except ImportError as e:
        logger.warning(f"Phase 3 Resource Lifecycle Management components not available: {e}")
        LIFECYCLE_MANAGEMENT_AVAILABLE = False

# Import original parallel processing components
try:
    from personal_trading_system.src.parallel.multi_process_scheduler import (
        MultiProcessScheduler, TaskPriority, Task, TaskStatus
    )
    from personal_trading_system.src.parallel.parallel_data_processor import (
        ParallelDataProcessor, DataChunk, ProcessingJob
    )
    from personal_trading_system.src.parallel.interprocess_communication import (
        InterProcessCommunication, MessageType, IPCMessage
    )
    from personal_trading_system.src.parallel.parallel_backtesting_engine import (
        ParallelBacktestingEngine, BacktestConfig, BacktestResult
    )
    from personal_trading_system.src.parallel.process_pool_manager import (
        ProcessPoolManager, WorkerState, WorkerMetrics
    )
    from personal_trading_system.src.parallel.memory_optimizer import (
        EnhancedMemoryOptimizer, MemoryPressureLevel
    )
    from personal_trading_system.src.parallel.result_aggregator import (
        ResultAggregator, AggregationConfig, PartialResult
    )
    from personal_trading_system.src.parallel.performance_monitor import (
        PerformanceMonitor, PerformanceMetric, AlertLevel
    )
    from personal_trading_system.src.parallel.system_optimizer import (
        SystemOptimizer, SystemTier, OptimizationConfig
    )
    ORIGINAL_COMPONENTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Original parallel components not available: {e}")
    ORIGINAL_COMPONENTS_AVAILABLE = False

# Import new memory management components
try:
    from src.memory import (
        AdaptiveMemoryAllocator, MemoryLeakDetector, MemoryPoolManager
    )
    NEW_MEMORY_MANAGEMENT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"New memory management components not available: {e}")
    NEW_MEMORY_MANAGEMENT_AVAILABLE = False

logger = logging.getLogger(__name__)

__version__ = "2.0.0"
__author__ = "Enhanced Parallel Processing Team"
__description__ = "High-performance 32-core parallel processing system with IPC synchronization"


class EnhancedParallelProcessingSystem:
    """
    Enhanced parallel processing system with IPC synchronization (Phase 2)

    New features in Phase 2:
    - AtomicInitializer: Eliminates race conditions during system startup
    - DeadlockDetector: Real-time deadlock detection and resolution
    - SmartMessageQueue: Advanced queuing with backpressure and retry logic
    - Feature flags for safe deployment
    - Comprehensive synchronization for 32-core concurrent processing
    """

    def __init__(
        self,
        max_workers: int = 32,
        memory_limit_gb: float = 64.0,
        enable_optimization: bool = True,
        enable_monitoring: bool = True,
        enable_profiling: bool = False,
        enable_new_memory_management: Optional[bool] = None,
        enable_ipc_enhancements: Optional[bool] = None,
        enable_atomic_initializer: Optional[bool] = None,
        enable_deadlock_detection: Optional[bool] = None,
        enable_smart_queuing: Optional[bool] = None,
        log_level: str = "INFO"
    ):
        """
        Initialize the enhanced parallel processing system

        Args:
            max_workers: Maximum number of worker processes
            memory_limit_gb: Memory limit in GB
            enable_optimization: Enable automatic system optimization
            enable_monitoring: Enable performance monitoring
            enable_profiling: Enable detailed profiling
            enable_new_memory_management: Enable new memory management features
            enable_ipc_enhancements: Enable IPC enhancements (None = auto-detect)
            enable_atomic_initializer: Enable atomic initializer (None = use feature flag)
            enable_deadlock_detection: Enable deadlock detection (None = use feature flag)
            enable_smart_queuing: Enable smart queuing (None = use feature flag)
            log_level: Logging level
        """
        self.max_workers = max_workers
        self.memory_limit_gb = memory_limit_gb
        self.enable_optimization = enable_optimization
        self.enable_monitoring = enable_monitoring
        self.enable_profiling = enable_profiling

        # Determine feature enablement
        self.enable_ipc_enhancements = (
            enable_ipc_enhancements if enable_ipc_enhancements is not None
            else ENABLE_IPC_ENHANCEMENTS
        ) and IPC_ENHANCEMENTS_AVAILABLE

        self.enable_atomic_initializer = (
            enable_atomic_initializer if enable_atomic_initializer is not None
            else ENABLE_ATOMIC_INITIALIZER
        ) and self.enable_ipc_enhancements

        self.enable_deadlock_detection = (
            enable_deadlock_detection if enable_deadlock_detection is not None
            else ENABLE_DEADLOCK_DETECTION
        ) and self.enable_ipc_enhancements

        self.enable_smart_queuing = (
            enable_smart_queuing if enable_smart_queuing is not None
            else ENABLE_SMART_QUEUING
        ) and self.enable_ipc_enhancements

        # Phase 3 feature enablement
        self.enable_lifecycle_manager = (
            ENABLE_LIFECYCLE_MANAGER and LIFECYCLE_MANAGEMENT_AVAILABLE
        )
        self.enable_zombie_detector = (
            ENABLE_ZOMBIE_DETECTOR and ZOMBIE_DETECTION_AVAILABLE
        )
        self.enable_resource_cleaner = (
            ENABLE_RESOURCE_CLEANER and RESOURCE_CLEANING_AVAILABLE
        )
        self.enable_graceful_shutdown = (
            ENABLE_GRACEFUL_SHUTDOWN and self.enable_lifecycle_manager
        )

        # New memory management components
        self.adaptive_allocator = None
        self.leak_detector = None
        self.pool_manager = None

        # New IPC synchronization components
        self.atomic_initializer: Optional[AtomicInitializer] = None
        self.deadlock_detector: Optional[DeadlockDetector] = None
        self.smart_message_queue: Optional[SmartMessageQueue] = None

        # Phase 3: Resource Lifecycle Management components
        self.lifecycle_manager: Optional[ProcessLifecycleManager] = None
        self.zombie_detector: Optional[ZombieProcessDetector] = None
        self.resource_cleaner: Optional[ResourceCleaner] = None

        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Original component instances (if available)
        self.scheduler = None
        self.data_processor = None
        self.ipc_system = None
        self.backtesting_engine = None
        self.process_pool = None
        self.memory_optimizer = None
        self.result_aggregator = None
        self.performance_monitor = None
        self.system_optimizer = None

        # System state
        self.is_initialized = False
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.optimization_config: Optional[OptimizationConfig] = None

        # Process information for atomic initialization
        self.process_id = os.getpid()
        self.total_processes = max_workers

        logger.info(f"EnhancedParallelProcessingSystem initialized:")
        logger.info(f"  - Workers: {max_workers}")
        logger.info(f"  - Memory: {memory_limit_gb}GB")
        logger.info(f"  - Atomic Initializer: {self.enable_atomic_initializer}")
        logger.info(f"  - Deadlock Detection: {self.enable_deadlock_detection}")
        logger.info(f"  - Smart Queuing: {self.enable_smart_queuing}")
        logger.info(f"  - IPC Enhancements: {self.enable_ipc_enhancements}")
        logger.info(f"  - Lifecycle Manager: {self.enable_lifecycle_manager}")
        logger.info(f"  - Zombie Detector: {self.enable_zombie_detector}")
        logger.info(f"  - Resource Cleaner: {self.enable_resource_cleaner}")
        logger.info(f"  - Graceful Shutdown: {self.enable_graceful_shutdown}")

    def initialize(self) -> bool:
        """
        Initialize all components using atomic initializer

        Returns:
            True if initialization successful
        """
        if self.is_initialized:
            logger.warning("System already initialized")
            return True

        logger.info("Initializing enhanced parallel processing system...")

        try:
            # Phase 1: Atomic initialization (if enabled)
            if self.enable_atomic_initializer:
                if not self._atomic_initialize():
                    logger.error("Atomic initialization failed")
                    return False
            else:
                if not self._legacy_initialize():
                    logger.error("Legacy initialization failed")
                    return False

            # Phase 2: Start IPC synchronization components
            if self.enable_ipc_enhancements:
                self._start_ipc_components()

            # Phase 3: Initialize Resource Lifecycle Management components
            if self.enable_lifecycle_manager or self.enable_zombie_detector or self.enable_resource_cleaner:
                if not self._init_lifecycle_management():
                    logger.error("Resource Lifecycle Management initialization failed")
                    return False

            self.is_initialized = True
            logger.info("Enhanced parallel processing system initialized successfully")
            return True

        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            return False

    def _atomic_initialize(self) -> bool:
        """Initialize using atomic initializer to eliminate race conditions"""
        try:
            logger.info("Starting atomic initialization...")

            # Create atomic initializer
            self.atomic_initializer = AtomicInitializer(
                process_id=self.process_id,
                total_processes=self.total_processes,
                enable_distributed_locking=True,
                enable_rollback=True
            )

            # Define component initialization tasks
            from src.ipc.atomic_initializer import ComponentInitTask, ComponentState

            component_tasks = []

            # System optimization task
            if self.enable_optimization and ORIGINAL_COMPONENTS_AVAILABLE:
                component_tasks.append(ComponentInitTask(
                    component_id="system_optimizer",
                    component_name="System Optimizer",
                    init_function=self._init_system_optimizer,
                    cleanup_function=self._cleanup_system_optimizer,
                    dependencies=set(),
                    priority=5,  # High priority
                    critical=True
                ))

            # Memory management task
            if self.enable_new_memory_management or ORIGINAL_COMPONENTS_AVAILABLE:
                component_tasks.append(ComponentInitTask(
                    component_id="memory_management",
                    component_name="Memory Management",
                    init_function=self._init_memory_management,
                    cleanup_function=self._cleanup_memory_management,
                    dependencies={"system_optimizer"} if self.enable_optimization else set(),
                    priority=4,
                    critical=True
                ))

            # IPC system task
            component_tasks.append(ComponentInitTask(
                component_id="ipc_system",
                component_name="IPC System",
                init_function=self._init_ipc_system,
                cleanup_function=self._cleanup_ipc_system,
                dependencies={"memory_management"},
                priority=3,
                critical=True
            ))

            # Scheduler task
            if ORIGINAL_COMPONENTS_AVAILABLE:
                component_tasks.append(ComponentInitTask(
                    component_id="scheduler",
                    component_name="Task Scheduler",
                    init_function=self._init_scheduler,
                    cleanup_function=self._cleanup_scheduler,
                    dependencies={"ipc_system", "memory_management"},
                    priority=2,
                    critical=True
                ))

            # Process pool task
            if ORIGINAL_COMPONENTS_AVAILABLE:
                component_tasks.append(ComponentInitTask(
                    component_id="process_pool",
                    component_name="Process Pool",
                    init_function=self._init_process_pool,
                    cleanup_function=self._cleanup_process_pool,
                    dependencies={"scheduler", "memory_management"},
                    priority=2,
                    critical=True
                ))

            # Data processor task
            if ORIGINAL_COMPONENTS_AVAILABLE:
                component_tasks.append(ComponentInitTask(
                    component_id="data_processor",
                    component_name="Data Processor",
                    init_function=self._init_data_processor,
                    cleanup_function=self._cleanup_data_processor,
                    dependencies={"scheduler", "process_pool"},
                    priority=1,
                    critical=False
                ))

            # Backtesting engine task
            if ORIGINAL_COMPONENTS_AVAILABLE:
                component_tasks.append(ComponentInitTask(
                    component_id="backtesting_engine",
                    component_name="Backtesting Engine",
                    init_function=self._init_backtesting_engine,
                    cleanup_function=self._cleanup_backtesting_engine,
                    dependencies={"data_processor", "process_pool"},
                    priority=1,
                    critical=False
                ))

            # Register all components with atomic initializer
            for task in component_tasks:
                self.atomic_initializer.register_component(task)

            # Perform atomic initialization
            return self.atomic_initializer.initialize()

        except Exception as e:
            logger.error(f"Atomic initialization failed: {e}")
            return False

    def _legacy_initialize(self) -> bool:
        """Legacy initialization without atomic initializer"""
        try:
            logger.info("Starting legacy initialization...")

            # Initialize components sequentially
            if self.enable_optimization and ORIGINAL_COMPONENTS_AVAILABLE:
                self._init_system_optimizer()

            self._init_memory_management()
            self._init_ipc_system()

            if ORIGINAL_COMPONENTS_AVAILABLE:
                self._init_scheduler()
                self._init_process_pool()
                self._init_data_processor()
                self._init_backtesting_engine()

            return True

        except Exception as e:
            logger.error(f"Legacy initialization failed: {e}")
            return False

    def _init_system_optimizer(self):
        """Initialize system optimizer"""
        if ORIGINAL_COMPONENTS_AVAILABLE:
            self.system_optimizer = SystemOptimizer(enable_detailed_profiling=self.enable_profiling)
            self.optimization_config = self.system_optimizer.optimize_system()
            # Apply system tuning
            self.system_optimizer.apply_tuning()

    def _cleanup_system_optimizer(self):
        """Cleanup system optimizer"""
        if self.system_optimizer:
            self.system_optimizer.cleanup()

    def _init_memory_management(self):
        """Initialize memory management components"""
        if self.enable_new_memory_management and NEW_MEMORY_MANAGEMENT_AVAILABLE:
            from src.memory import create_adaptive_allocator, create_leak_detector, create_pool_manager

            self.adaptive_allocator = create_adaptive_allocator(
                total_memory_gb=self.memory_limit_gb,
                enable_monitoring=True
            )

            self.leak_detector = create_leak_detector(
                detection_threshold_mb=100.0,
                monitoring_interval=30.0
            )

            self.pool_manager = create_pool_manager(
                max_pools=50,
                max_total_memory_mb=self.memory_limit_gb * 1024
            )

        elif ORIGINAL_COMPONENTS_AVAILABLE:
            # Fall back to original memory optimizer
            from personal_trading_system.src.parallel.memory_optimizer import EnhancedMemoryOptimizer
            self.memory_optimizer = EnhancedMemoryOptimizer(
                target_memory_usage_percent=75.0,
                gc_threshold_percent=85.0,
                max_memory_pool_mb=self.memory_limit_gb * 2,
                total_memory_gb=self.memory_limit_gb
            )

    def _cleanup_memory_management(self):
        """Cleanup memory management components"""
        if self.adaptive_allocator:
            self.adaptive_allocator.cleanup()
        if self.leak_detector:
            self.leak_detector.stop()
        if self.pool_manager:
            self.pool_manager.cleanup()
        if self.memory_optimizer:
            self.memory_optimizer.stop()

    def _init_ipc_system(self):
        """Initialize IPC system"""
        if self.enable_smart_queuing:
            # Initialize smart message queue
            self.smart_message_queue = SmartMessageQueue(
                max_size=10000,
                enable_backpressure=True,
                enable_metrics=True
            )
            self.smart_message_queue.start()

        if ORIGINAL_COMPONENTS_AVAILABLE:
            # Initialize original IPC system
            from personal_trading_system.src.parallel.interprocess_communication import InterProcessCommunication
            self.ipc_system = InterProcessCommunication(
                process_id=0,
                max_shared_memory_mb=int(self.memory_limit_gb * 512)
            )

    def _cleanup_ipc_system(self):
        """Cleanup IPC system"""
        if self.smart_message_queue:
            self.smart_message_queue.stop()
        if self.ipc_system:
            self.ipc_system.stop()

    def _init_scheduler(self):
        """Initialize task scheduler"""
        if ORIGINAL_COMPONENTS_AVAILABLE:
            from personal_trading_system.src.parallel.multi_process_scheduler import MultiProcessScheduler
            self.scheduler = MultiProcessScheduler(
                max_workers=self.max_workers,
                memory_limit_gb=self.memory_limit_gb
            )

    def _cleanup_scheduler(self):
        """Cleanup task scheduler"""
        if self.scheduler:
            self.scheduler.stop()

    def _init_process_pool(self):
        """Initialize process pool"""
        if ORIGINAL_COMPONENTS_AVAILABLE:
            from personal_trading_system.src.parallel.process_pool_manager import ProcessPoolManager
            self.process_pool = ProcessPoolManager(
                min_workers=max(4, self.max_workers // 8),
                max_workers=self.max_workers,
                memory_threshold_mb=self.memory_limit_gb * 1024 * 0.1
            )

    def _cleanup_process_pool(self):
        """Cleanup process pool"""
        if self.process_pool:
            self.process_pool.stop()

    def _init_data_processor(self):
        """Initialize data processor"""
        if ORIGINAL_COMPONENTS_AVAILABLE:
            from personal_trading_system.src.parallel.parallel_data_processor import ParallelDataProcessor
            self.data_processor = ParallelDataProcessor(
                scheduler=self.scheduler,
                max_chunk_size_mb=int(self.memory_limit_gb * 1024 / self.max_workers)
            )

    def _cleanup_data_processor(self):
        """Cleanup data processor"""
        if self.data_processor:
            self.data_processor.cleanup()

    def _init_backtesting_engine(self):
        """Initialize backtesting engine"""
        if ORIGINAL_COMPONENTS_AVAILABLE:
            from personal_trading_system.src.parallel.parallel_backtesting_engine import ParallelBacktestingEngine, BacktestConfig
            self.backtesting_engine = ParallelBacktestingEngine(
                config=BacktestConfig(
                    symbols=[],
                    start_date=datetime.now() - timedelta(days=365),
                    end_date=datetime.now(),
                    num_workers=self.max_workers,
                    memory_limit_gb=self.memory_limit_gb
                ),
                scheduler=self.scheduler,
                data_processor=self.data_processor
            )

    def _cleanup_backtesting_engine(self):
        """Cleanup backtesting engine"""
        if self.backtesting_engine:
            self.backtesting_engine.cleanup()

    def _start_ipc_components(self):
        """Start IPC synchronization components"""
        try:
            # Start deadlock detector
            if self.enable_deadlock_detection:
                self.deadlock_detector = DeadlockDetector(
                    detection_interval_seconds=1.0,
                    enable_auto_resolution=True
                )
                self.deadlock_detector.start()

                # Register current process
                from src.ipc.deadlock_detector import Priority
                self.deadlock_detector.register_process(self.process_id, Priority.HIGH)

            logger.info("IPC synchronization components started")

        except Exception as e:
            logger.error(f"Failed to start IPC components: {e}")

    def _init_lifecycle_management(self) -> bool:
        """Initialize Phase 3 Resource Lifecycle Management components"""
        try:
            logger.info("Initializing Resource Lifecycle Management components...")

            # Initialize Process Lifecycle Manager
            if self.enable_lifecycle_manager:
                config = LifecycleConfig(
                    preparation_timeout=5.0,
                    graceful_stop_timeout=20.0,
                    force_termination_timeout=5.0,
                    cleanup_validation_timeout=3.0,
                    enable_signal_handlers=True,
                    enable_auto_recovery=True
                )
                self.lifecycle_manager = ProcessLifecycleManager(
                    config=config,
                    max_workers=self.max_workers
                )
                logger.info("Process Lifecycle Manager initialized")

            # Initialize Zombie Process Detector
            if self.enable_zombie_detector:
                config = DetectorConfig(
                    scan_interval=2.0,
                    enable_auto_cleanup=True,
                    cleanup_retry_attempts=3,
                    alert_threshold_zombies=5
                )
                # Get managed processes mapping if available
                managed_processes = {}
                if ORIGINAL_COMPONENTS_AVAILABLE and self.process_pool:
                    # Extract worker PID mappings from process pool
                    managed_processes = getattr(self.process_pool, 'worker_pids', {})

                self.zombie_detector = ZombieProcessDetector(
                    config=config,
                    managed_processes=managed_processes
                )
                logger.info("Zombie Process Detector initialized")

            # Initialize Resource Cleaner
            if self.enable_resource_cleaner:
                config = CleanerConfig(
                    cleanup_timeout=30.0,
                    enable_cleanup_validation=True,
                    enable_monitoring=True,
                    cleanup_on_exit=True
                )
                self.resource_cleaner = ResourceCleaner(config=config)
                logger.info("Resource Cleaner initialized")

            logger.info("Resource Lifecycle Management components initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Resource Lifecycle Management: {e}")
            return False

    def start(self):
        """Start all components"""
        if not self.is_initialized:
            raise RuntimeError("System not initialized. Call initialize() first.")

        if self.is_running:
            logger.warning("System already running")
            return

        logger.info("Starting enhanced parallel processing system...")

        self.start_time = datetime.now()

        try:
            # Start original components
            if ORIGINAL_COMPONENTS_AVAILABLE:
                if self.memory_optimizer:
                    self.memory_optimizer.start()
                if self.ipc_system:
                    self.ipc_system.start()
                if self.scheduler:
                    self.scheduler.start()
                if self.process_pool:
                    self.process_pool.start()

            # Start Phase 3 Resource Lifecycle Management components
            if self.lifecycle_manager:
                self.lifecycle_manager.start_monitoring()

            if self.zombie_detector:
                self.zombie_detector.start_monitoring()

            if self.resource_cleaner:
                self.resource_cleaner.start_monitoring()

            self.is_running = True
            logger.info("Enhanced parallel processing system started successfully")

        except Exception as e:
            logger.error(f"Failed to start system: {e}")
            self.stop()
            raise

    def stop(self, timeout: float = 30.0):
        """Stop all components with graceful shutdown"""
        if not self.is_running:
            return

        logger.info("Stopping enhanced parallel processing system...")

        try:
            # Use Phase 3 graceful shutdown if available
            if self.enable_graceful_shutdown and self.lifecycle_manager:
                logger.info("Initiating Phase 3 graceful shutdown...")
                success = self.lifecycle_manager.graceful_shutdown(timeout=timeout)
                if not success:
                    logger.warning("Graceful shutdown failed, falling back to manual cleanup")

            # Stop Phase 3 Resource Lifecycle Management components
            if self.resource_cleaner:
                self.resource_cleaner.cleanup_all_resources(force=True)
                self.resource_cleaner.stop_monitoring()

            if self.zombie_detector:
                self.zombie_detector.force_cleanup_all_zombies()
                self.zombie_detector.stop_monitoring()

            if self.lifecycle_manager:
                self.lifecycle_manager.stop_monitoring()

            # Stop IPC components
            if self.deadlock_detector:
                self.deadlock_detector.unregister_process(self.process_id)
                self.deadlock_detector.stop()

            if self.smart_message_queue:
                self.smart_message_queue.stop()

            # Stop original components
            if ORIGINAL_COMPONENTS_AVAILABLE:
                if self.process_pool:
                    self.process_pool.stop()
                if self.scheduler:
                    self.scheduler.stop()
                if self.memory_optimizer:
                    self.memory_optimizer.stop()
                if self.ipc_system:
                    self.ipc_system.stop()

            # Stop atomic initializer
            if self.atomic_initializer:
                self.atomic_initializer.cleanup()

            self.is_running = False
            logger.info("Enhanced parallel processing system stopped")

        except Exception as e:
            logger.error(f"Error stopping system: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            'is_initialized': self.is_initialized,
            'is_running': self.is_running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            'max_workers': self.max_workers,
            'memory_limit_gb': self.memory_limit_gb,
            'process_id': self.process_id,
            'features_enabled': {
                'atomic_initializer': self.enable_atomic_initializer,
                'deadlock_detection': self.enable_deadlock_detection,
                'smart_queuing': self.enable_smart_queuing,
                'ipc_enhancements': self.enable_ipc_enhancements,
                'lifecycle_manager': self.enable_lifecycle_manager,
                'zombie_detector': self.enable_zombie_detector,
                'resource_cleaner': self.enable_resource_cleaner,
                'graceful_shutdown': self.enable_graceful_shutdown
            }
        }

        # Add component-specific status
        if self.atomic_initializer:
            status['atomic_initializer_status'] = self.atomic_initializer.get_initialization_status()

        if self.deadlock_detector:
            status['deadlock_detector_stats'] = self.deadlock_detector.get_statistics()

        if self.smart_message_queue:
            status['smart_queue_status'] = self.smart_message_queue.get_status()

        # Add Phase 3 component stats
        if self.lifecycle_manager:
            status['lifecycle_manager_status'] = self.lifecycle_manager.get_status()
            status['lifecycle_manager_metrics'] = self.lifecycle_manager.get_shutdown_metrics()

        if self.zombie_detector:
            status['zombie_detector_stats'] = self.zombie_detector.get_statistics()

        if self.resource_cleaner:
            status['resource_cleaner_stats'] = self.resource_cleaner.get_statistics()

        # Add original component stats
        if ORIGINAL_COMPONENTS_AVAILABLE and self.is_running:
            status.update({
                'scheduler_stats': self.scheduler.get_statistics() if self.scheduler else {},
                'memory_optimizer_stats': self.memory_optimizer.get_statistics() if self.memory_optimizer else {},
            })

        return status

    def __enter__(self):
        """Context manager entry"""
        if not self.is_initialized:
            self.initialize()
        if not self.is_running:
            self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


# Convenience functions with enhanced features
def create_enhanced_parallel_system(
    max_workers: int = 32,
    memory_limit_gb: float = 64.0,
    **kwargs
) -> EnhancedParallelProcessingSystem:
    """
    Create and initialize an enhanced parallel processing system

    Args:
        max_workers: Maximum number of worker processes
        memory_limit_gb: Memory limit in GB
        **kwargs: Additional system parameters

    Returns:
        Initialized EnhancedParallelProcessingSystem
    """
    system = EnhancedParallelProcessingSystem(
        max_workers=max_workers,
        memory_limit_gb=memory_limit_gb,
        **kwargs
    )
    system.initialize()
    return system


# Export main classes and functions
__all__ = [
    # Main enhanced system
    'EnhancedParallelProcessingSystem',
    'create_enhanced_parallel_system',

    # IPC synchronization components
    'AtomicInitializer',
    'DeadlockDetector',
    'SmartMessageQueue',

    # Phase 3 Resource Lifecycle Management components
    'ProcessLifecycleManager',
    'ZombieProcessDetector',
    'ResourceCleaner',

    # Feature flags
    'ENABLE_ATOMIC_INITIALIZER',
    'ENABLE_DEADLOCK_DETECTION',
    'ENABLE_SMART_QUEUING',
    'ENABLE_IPC_ENHANCEMENTS',
    'ENABLE_LIFECYCLE_MANAGER',
    'ENABLE_ZOMBIE_DETECTOR',
    'ENABLE_RESOURCE_CLEANER',
    'ENABLE_GRACEFUL_SHUTDOWN',

    # Component availability flags
    'IPC_ENHANCEMENTS_AVAILABLE',
    'LIFECYCLE_MANAGEMENT_AVAILABLE',
    'ZOMBIE_DETECTION_AVAILABLE',
    'RESOURCE_CLEANING_AVAILABLE',

    # Original components (for backward compatibility)
    'ParallelProcessingSystem' if ORIGINAL_COMPONENTS_AVAILABLE else None,
    'MultiProcessScheduler' if ORIGINAL_COMPONENTS_AVAILABLE else None,
    'ParallelDataProcessor' if ORIGINAL_COMPONENTS_AVAILABLE else None,
    'InterProcessCommunication' if ORIGINAL_COMPONENTS_AVAILABLE else None,
    'ParallelBacktestingEngine' if ORIGINAL_COMPONENTS_AVAILABLE else None,

    # Metadata
    '__version__',
    '__author__',
    '__description__',
]

logger.info(f"Enhanced Parallel Processing System v{__version__} loaded successfully")
logger.info(f"Phase 2 Features - Atomic Initializer: {ENABLE_ATOMIC_INITIALIZER}, "
           f"Deadlock Detection: {ENABLE_DEADLOCK_DETECTION}, "
           f"Smart Queuing: {ENABLE_SMART_QUEUING}, "
           f"IPC Enhancements: {ENABLE_IPC_ENHANCEMENTS}")
logger.info(f"Phase 3 Features - Lifecycle Manager: {ENABLE_LIFECYCLE_MANAGER}, "
           f"Zombie Detector: {ENABLE_ZOMBIE_DETECTOR}, "
           f"Resource Cleaner: {ENABLE_RESOURCE_CLEANER}, "
           f"Graceful Shutdown: {ENABLE_GRACEFUL_SHUTDOWN}")
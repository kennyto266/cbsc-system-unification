#!/usr/bin/env python3
"""
Parallel Processing System for 32-Core CPU Backtesting
Main integration module for high-performance parallel processing
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import all parallel processing components
from .multi_process_scheduler import MultiProcessScheduler, TaskPriority, Task, TaskStatus, chunk_data, estimate_task_memory
from .parallel_data_processor import ParallelDataProcessor, DataChunk, ProcessingJob, processing_functions
from .interprocess_communication import InterProcessCommunication, MessageType, IPCMessage, create_ipc_systems
from .parallel_backtesting_engine import ParallelBacktestingEngine, BacktestConfig, BacktestResult, simple_ma_crossover_strategy, rsi_mean_reversion_strategy
from .process_pool_manager import ProcessPoolManager, DynamicLoadBalancer, WorkerState, WorkerMetrics
from .memory_optimizer import EnhancedMemoryOptimizer, MemoryPressureLevel, get_optimal_system_config

# Import new memory management components
try:
    from src.memory import (
        AdaptiveMemoryAllocator, MemoryLeakDetector, MemoryPoolManager,
        create_adaptive_allocator, calculate_memory_allocation
    )
    NEW_MEMORY_MANAGEMENT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"New memory management components not available: {e}")
    NEW_MEMORY_MANAGEMENT_AVAILABLE = False
from .result_aggregator import ResultAggregator, AggregationConfig, PartialResult, AggregationJob
from .performance_monitor import PerformanceMonitor, PerformanceMetric, AlertLevel
from .system_optimizer import SystemOptimizer, SystemTier, OptimizationConfig, apply_system_tuning

logger = logging.getLogger(__name__)

__version__ = "1.0.0"
__author__ = "Parallel Processing Team"
__description__ = "High-performance 32-core CPU parallel processing system for quantitative backtesting"


class ParallelProcessingSystem:
    """
    Main interface for the complete parallel processing system

    This class provides a unified interface to all parallel processing components
    and manages their lifecycle and interactions.

    Features:
    - Unified 32-core parallel processing platform
    - Automatic system optimization and tuning
    - Component lifecycle management
    - Performance monitoring and alerting
    - Fault tolerance and recovery
    - Comprehensive statistics and reporting
    - Easy-to-use high-level API
    """

    def __init__(
        self,
        max_workers: int = 32,
        memory_limit_gb: float = 64.0,
        enable_optimization: bool = True,
        enable_monitoring: bool = True,
        enable_profiling: bool = False,
        enable_new_memory_management: Optional[bool] = None,
        log_level: str = "INFO"
    ):
        """
        Initialize the parallel processing system

        Args:
            max_workers: Maximum number of worker processes
            memory_limit_gb: Memory limit in GB
            enable_optimization: Enable automatic system optimization
            enable_monitoring: Enable performance monitoring
            enable_profiling: Enable detailed profiling
            enable_new_memory_management: Enable new memory management features (None = auto-detect)
            log_level: Logging level
        """
        self.max_workers = max_workers
        self.memory_limit_gb = memory_limit_gb
        self.enable_optimization = enable_optimization
        self.enable_monitoring = enable_monitoring
        self.enable_profiling = enable_profiling

        # Determine if new memory management should be enabled
        if enable_new_memory_management is None:
            self.enable_new_memory_management = NEW_MEMORY_MANAGEMENT_AVAILABLE
        else:
            self.enable_new_memory_management = enable_new_memory_management and NEW_MEMORY_MANAGEMENT_AVAILABLE

        # New memory management components
        self.adaptive_allocator = None
        self.leak_detector = None
        self.pool_manager = None

        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Component instances
        self.scheduler: Optional[MultiProcessScheduler] = None
        self.data_processor: Optional[ParallelDataProcessor] = None
        self.ipc_system: Optional[InterProcessCommunication] = None
        self.backtesting_engine: Optional[ParallelBacktestingEngine] = None
        self.process_pool: Optional[ProcessPoolManager] = None
        self.memory_optimizer: Optional[EnhancedMemoryOptimizer] = None
        self.result_aggregator: Optional[ResultAggregator] = None
        self.performance_monitor: Optional[PerformanceMonitor] = None
        self.system_optimizer: Optional[SystemOptimizer] = None

        # System state
        self.is_initialized = False
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.optimization_config: Optional[OptimizationConfig] = None

        logger.info(f"ParallelProcessingSystem initialized with {max_workers} workers, "
                   f"new memory management: {self.enable_new_memory_management}")

    def initialize(self) -> bool:
        """
        Initialize all parallel processing components

        Returns:
            True if initialization successful
        """
        if self.is_initialized:
            logger.warning("System already initialized")
            return True

        logger.info("Initializing parallel processing system...")

        try:
            # Initialize new memory management components first
            if self.enable_new_memory_management:
                self._initialize_new_memory_management()

            # System optimization first
            if self.enable_optimization:
                self.system_optimizer = SystemOptimizer(enable_detailed_profiling=self.enable_profiling)
                self.optimization_config = self.system_optimizer.optimize_system()
                apply_system_tuning()

            # Initialize core components
            self.scheduler = MultiProcessScheduler(
                max_workers=self.max_workers,
                memory_limit_gb=self.memory_limit_gb
            )

            self.data_processor = ParallelDataProcessor(
                scheduler=self.scheduler,
                max_chunk_size_mb=int(self.memory_limit_gb * 1024 / self.max_workers)
            )

            # Calculate optimal memory allocation using new system
            if self.enable_new_memory_management and self.adaptive_allocator:
                optimal_allocation = self.adaptive_allocator.calculate_optimal_allocation(
                    data_size_mb=1024,  # Default 1GB data size
                    concurrent_processes=self.max_workers,
                    task_type="parallel_processing"
                )
                shared_memory_mb = optimal_allocation.shared_memory_mb
                logger.info(f"Using adaptive memory allocation: {shared_memory_mb}MB shared memory, "
                           f"strategy: {optimal_allocation.strategy_used.value}")
            else:
                # Fallback to original hardcoded allocation
                shared_memory_mb = int(self.memory_limit_gb * 512)  # Half for shared memory
                logger.warning(f"Using fallback memory allocation: {shared_memory_mb}MB shared memory")

            self.ipc_system = InterProcessCommunication(
                process_id=0,
                max_shared_memory_mb=shared_memory_mb
            )

            self.process_pool = ProcessPoolManager(
                min_workers=max(4, self.max_workers // 8),
                max_workers=self.max_workers,
                memory_threshold_mb=self.memory_limit_gb * 1024 * 0.1
            )

            self.memory_optimizer = EnhancedMemoryOptimizer(
                target_memory_usage_percent=75.0,
                gc_threshold_percent=85.0,
                max_memory_pool_mb=self.memory_limit_gb * 2,
                total_memory_gb=self.memory_limit_gb,
                enable_new_features=self.enable_new_memory_management
            )

            self.result_aggregator = ResultAggregator(
                config=AggregationConfig(
                    max_concurrent_jobs=self.max_workers * 4,
                    default_timeout_seconds=300.0,
                    enable_compression=True,
                    max_memory_pool_mb=self.memory_limit_gb
                ),
                ipc_system=self.ipc_system
            )

            self.performance_monitor = PerformanceMonitor(
                sampling_interval=1.0,
                history_size=1000,
                enable_profiling=self.enable_profiling
            )

            # Register components with monitoring
            self.performance_monitor.register_component("scheduler", self.scheduler)
            self.performance_monitor.register_component("data_processor", self.data_processor)
            self.performance_monitor.register_component("memory_optimizer", self.memory_optimizer)

            # Initialize backtesting engine
            self.backtesting_engine = ParallelBacktestingEngine(
                config=BacktestConfig(
                    symbols=[],  # Will be set per backtest
                    start_date=datetime.now() - timedelta(days=365),
                    end_date=datetime.now(),
                    num_workers=self.max_workers,
                    memory_limit_gb=self.memory_limit_gb
                ),
                scheduler=self.scheduler,
                data_processor=self.data_processor
            )

            self.is_initialized = True
            logger.info("Parallel processing system initialized successfully")

            return True

        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            return False

    def start(self):
        """Start all parallel processing components"""
        if not self.is_initialized:
            raise RuntimeError("System not initialized. Call initialize() first.")

        if self.is_running:
            logger.warning("System already running")
            return

        logger.info("Starting parallel processing system...")

        self.start_time = datetime.now()

        try:
            # Start components in dependency order
            self.memory_optimizer.start()
            self.ipc_system.start()
            self.scheduler.start()
            self.process_pool.start()
            self.result_aggregator.start()
            self.performance_monitor.start()

            self.is_running = True
            logger.info("Parallel processing system started successfully")

        except Exception as e:
            logger.error(f"Failed to start system: {e}")
            self.stop()
            raise

    def stop(self, timeout: float = 30.0):
        """Stop all parallel processing components"""
        if not self.is_running:
            return

        logger.info("Stopping parallel processing system...")

        try:
            # Stop components in reverse order
            if self.performance_monitor:
                self.performance_monitor.stop()

            if self.result_aggregator:
                self.result_aggregator.stop()

            if self.process_pool:
                self.process_pool.stop()

            if self.scheduler:
                self.scheduler.stop()

            if self.memory_optimizer:
                self.memory_optimizer.stop()

            if self.ipc_system:
                self.ipc_system.stop()

            self.is_running = False
            logger.info("Parallel processing system stopped")

        except Exception as e:
            logger.error(f"Error stopping system: {e}")

    def submit_task(
        self,
        function: Callable,
        args: tuple = (),
        kwargs: dict = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        estimated_memory_mb: int = 100,
        estimated_cpu_time: float = 1.0
    ) -> str:
        """
        Submit a task for parallel execution

        Args:
            function: Function to execute
            args: Function arguments
            kwargs: Function keyword arguments
            priority: Task priority
            estimated_memory_mb: Estimated memory usage
            estimated_cpu_time: Estimated CPU time

        Returns:
            Task ID
        """
        if not self.is_running:
            raise RuntimeError("System not running. Call start() first.")

        return self.scheduler.submit_task(
            function=function,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            estimated_memory_mb=estimated_memory_mb,
            estimated_cpu_time=estimated_cpu_time
        )

    def process_data_parallel(
        self,
        data: Any,
        processing_function: str,
        processing_args: tuple = (),
        processing_kwargs: dict = None,
        chunk_size: Optional[int] = None,
        merge_results: bool = True
    ) -> Any:
        """
        Process data in parallel

        Args:
            data: Data to process
            processing_function: Name of processing function
            processing_args: Arguments for processing function
            processing_kwargs: Keyword arguments for processing function
            chunk_size: Size of each chunk (auto-calculated if None)
            merge_results: Whether to merge results

        Returns:
            Processing results
        """
        if not self.is_running:
            raise RuntimeError("System not running. Call start() first.")

        return self.data_processor.process_data_parallel(
            data=data,
            processing_function=processing_function,
            processing_args=processing_args,
            processing_kwargs=processing_kwargs or {},
            chunk_size=chunk_size,
            merge_results=merge_results
        )

    def run_backtest(
        self,
        data: Any,
        strategy_function: Callable,
        symbols: List[str] = None,
        start_date: datetime = None,
        end_date: datetime = None,
        strategy_params: dict = None,
        **kwargs
    ) -> BacktestResult:
        """
        Run parallel backtesting

        Args:
            data: Backtesting data
            strategy_function: Strategy function
            symbols: List of symbols to backtest
            start_date: Backtest start date
            end_date: Backtest end date
            strategy_params: Strategy parameters
            **kwargs: Additional backtesting parameters

        Returns:
            BacktestResult with comprehensive metrics
        """
        if not self.is_running:
            raise RuntimeError("System not running. Call start() first.")

        # Update backtesting engine configuration
        if symbols:
            self.backtesting_engine.config.symbols = symbols
        if start_date:
            self.backtesting_engine.config.start_date = start_date
        if end_date:
            self.backtesting_engine.config.end_date = end_date

        return self.backtesting_engine.run_parallel_backtest(
            data=data,
            strategy_function=strategy_function,
            strategy_params=strategy_params or {},
            **kwargs
        )

    def run_parameter_sweep(
        self,
        data: Any,
        strategy_function: Callable,
        parameter_grid: Dict[str, List[Any]],
        combination_limit: Optional[int] = None
    ) -> List[BacktestResult]:
        """
        Run parameter optimization sweep

        Args:
            data: Backtesting data
            strategy_function: Strategy function
            parameter_grid: Parameter combinations to test
            combination_limit: Limit number of combinations

        Returns:
            List of BacktestResult sorted by performance
        """
        if not self.is_running:
            raise RuntimeError("System not running. Call start() first.")

        return self.backtesting_engine.run_parameter_sweep(
            data=data,
            strategy_function=strategy_function,
            parameter_grid=parameter_grid,
            combination_limit=combination_limit
        )

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            'is_initialized': self.is_initialized,
            'is_running': self.is_running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            'max_workers': self.max_workers,
            'memory_limit_gb': self.memory_limit_gb
        }

        if self.is_running:
            # Add component statistics
            status.update({
                'scheduler_stats': self.scheduler.get_statistics() if self.scheduler else {},
                'data_processor_stats': self.data_processor.get_statistics() if self.data_processor else {},
                'memory_optimizer_stats': self.memory_optimizer.get_statistics() if self.memory_optimizer else {},
                'performance_monitor_stats': self.performance_monitor.get_statistics() if self.performance_monitor else {}
            })

            # Add real-time metrics
            status['real_time_metrics'] = self.performance_monitor.get_real_time_metrics() if self.performance_monitor else {}

        return status

    def generate_report(self, format: str = 'json') -> str:
        """Generate comprehensive system report"""
        if not self.is_running:
            return "System not running"

        # Collect data from all components
        report_data = {
            'system_info': {
                'version': __version__,
                'description': __description__,
                'author': __author__,
                'timestamp': datetime.now().isoformat()
            },
            'system_status': self.get_system_status(),
            'optimization_config': self.optimization_config.__dict__ if self.optimization_config else None,
            'performance_report': self.performance_monitor.generate_performance_report(format='dict') if self.performance_monitor else {}
        }

        if format.lower() == 'json':
            import json
            return json.dumps(report_data, indent=2, default=str)
        else:
            # Simple text format
            lines = [
                "PARALLEL PROCESSING SYSTEM REPORT",
                "=" * 50,
                f"Version: {__version__}",
                f"Author: {__author__}",
                f"Timestamp: {report_data['system_info']['timestamp']}",
                "",
                "SYSTEM STATUS:",
                "-" * 20,
                f"Initialized: {report_data['system_status']['is_initialized']}",
                f"Running: {report_data['system_status']['is_running']}",
                f"Workers: {report_data['system_status']['max_workers']}",
                f"Memory Limit: {report_data['system_status']['memory_limit_gb']}GB",
            ]

            return "\n".join(lines)

    def optimize_memory(self, force: bool = False):
        """Force memory optimization"""
        if not self.is_running:
            raise RuntimeError("System not running. Call start() first.")

        return self.memory_optimizer.optimize_memory(force=force)

    def get_optimization_recommendations(self) -> Dict[str, Any]:
        """Get system optimization recommendations"""
        if not self.system_optimizer:
            return {}

        return self.system_optimizer.generate_optimization_report()

    def __enter__(self):
        """Context manager entry"""
        if not self.is_initialized:
            self.initialize()
        if not self.is_running:
            self.start()
        return self

    def _initialize_new_memory_management(self):
        """Initialize new memory management components"""
        try:
            # Initialize adaptive memory allocator
            self.adaptive_allocator = create_adaptive_allocator(
                total_memory_gb=self.memory_limit_gb,
                enable_monitoring=True,
                safety_margin_percent=15.0
            )

            # Initialize memory leak detector
            self.leak_detector = create_leak_detector(
                detection_threshold_mb=100.0,
                monitoring_interval=30.0,
                enable_object_tracking=True
            )

            # Initialize memory pool manager
            self.pool_manager = create_pool_manager(
                max_pools=50,
                max_total_memory_mb=self.memory_limit_gb * 1024,
                auto_defragment=True,
                enable_backup=True
            )

            logger.info("New memory management components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize new memory management: {e}")
            self.enable_new_memory_management = False

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


# Convenience functions for quick usage
def create_parallel_system(
    max_workers: int = 32,
    memory_limit_gb: float = 64.0,
    **kwargs
) -> ParallelProcessingSystem:
    """
    Create and initialize a parallel processing system

    Args:
        max_workers: Maximum number of worker processes
        memory_limit_gb: Memory limit in GB
        **kwargs: Additional system parameters

    Returns:
        Initialized ParallelProcessingSystem
    """
    system = ParallelProcessingSystem(
        max_workers=max_workers,
        memory_limit_gb=memory_limit_gb,
        **kwargs
    )
    system.initialize()
    return system


def quick_backtest(
    data: Any,
    strategy_function: Callable,
    symbols: List[str] = None,
    max_workers: int = 32,
    **kwargs
) -> BacktestResult:
    """
    Quick backtest with automatic system setup

    Args:
        data: Backtesting data
        strategy_function: Strategy function
        symbols: List of symbols
        max_workers: Number of workers
        **kwargs: Additional backtesting parameters

    Returns:
        BacktestResult
    """
    with create_parallel_system(max_workers=max_workers) as system:
        return system.run_backtest(
            data=data,
            strategy_function=strategy_function,
            symbols=symbols,
            **kwargs
        )


def quick_parameter_sweep(
    data: Any,
    strategy_function: Callable,
    parameter_grid: Dict[str, List[Any]],
    max_workers: int = 32,
    **kwargs
) -> List[BacktestResult]:
    """
    Quick parameter sweep with automatic system setup

    Args:
        data: Backtesting data
        strategy_function: Strategy function
        parameter_grid: Parameter combinations to test
        max_workers: Number of workers
        **kwargs: Additional parameters

    Returns:
        List of BacktestResult sorted by performance
    """
    with create_parallel_system(max_workers=max_workers) as system:
        return system.run_parameter_sweep(
            data=data,
            strategy_function=strategy_function,
            parameter_grid=parameter_grid,
            **kwargs
        )


# Export main classes and functions
__all__ = [
    # Main system class
    'ParallelProcessingSystem',

    # Core components
    'MultiProcessScheduler',
    'ParallelDataProcessor',
    'InterProcessCommunication',
    'ParallelBacktestingEngine',
    'ProcessPoolManager',
    'EnhancedMemoryOptimizer',
    'MemoryOptimizer',  # Backward compatibility
    'ResultAggregator',
    'PerformanceMonitor',
    'SystemOptimizer',

    # Configuration classes
    'TaskPriority',
    'TaskStatus',
    'BacktestConfig',
    'AggregationConfig',

    # Convenience functions
    'create_parallel_system',
    'quick_backtest',
    'quick_parameter_sweep',
    'get_optimal_system_config',
    'apply_system_tuning',

    # Utility functions
    'chunk_data',
    'estimate_task_memory',

    # Strategy examples
    'simple_ma_crossover_strategy',
    'rsi_mean_reversion_strategy',

    # Processing functions
    'processing_functions',

    # Metadata
    '__version__',
    '__author__',
    '__description__'
]

logger.info(f"ParallelProcessingSystem v{__version__} loaded successfully")
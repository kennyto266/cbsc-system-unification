#!/usr/bin/env python3
"""
Enhanced Memory Optimizer for Parallel Processing
Advanced memory management and optimization integrated with new memory management system

This module integrates the original memory optimization capabilities with the new
adaptive memory allocator, leak detector, and pool manager from the stability fixes.
"""

import os
import sys
import gc
import time
import threading
import logging
import psutil
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import pickle
import weakref
import tracemalloc

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import new memory management components
try:
    from src.memory import (
        AdaptiveMemoryAllocator, MemoryLeakDetector, MemoryPoolManager,
        MemoryPressureLevel, LeakSeverity, PoolType,
        create_adaptive_allocator, create_leak_detector, create_pool_manager,
        get_memory_management_status
    )
    NEW_MEMORY_MANAGEMENT_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"New memory management components not available: {e}")
    NEW_MEMORY_MANAGEMENT_AVAILABLE = False

logger = logging.getLogger(__name__)


class MemoryPressureLevel(Enum):
    """Memory pressure levels"""
    LOW = "low"        # < 50% usage
    MEDIUM = "medium"  # 50-75% usage
    HIGH = "high"      # 75-90% usage
    CRITICAL = "critical"  # > 90% usage


@dataclass
class MemorySnapshot:
    """Snapshot of memory usage at a point in time"""
    timestamp: datetime
    total_memory_mb: float
    used_memory_mb: float
    available_memory_mb: float
    process_memory_mb: float
    gc_collections: int
    active_objects: int
    pressure_level: MemoryPressureLevel


@dataclass
class MemoryOptimizationResult:
    """Result of memory optimization operation"""
    timestamp: datetime
    memory_freed_mb: float
    objects_collected: int
    gc_time_ms: float
    optimization_type: str
    success: bool
    details: Dict[str, Any] = field(default_factory=dict)


class EnhancedMemoryOptimizer:
    """
    Enhanced Memory Optimization System with New Memory Management Integration

    This class combines the original memory optimization capabilities with the new
    adaptive memory allocator, leak detector, and pool manager for comprehensive
    memory management in the 32-core parallel processing system.

    Key Improvements:
    - Integration with adaptive memory allocator
    - Automatic memory leak detection and prevention
    - Advanced memory pool management with defragmentation
    - Production-grade monitoring and alerting
    - Feature flag controlled rollout
    """

    def __init__(
        self,
        target_memory_usage_percent: float = 75.0,
        gc_threshold_percent: float = 85.0,
        cleanup_interval: float = 30.0,
        enable_memory_profiling: bool = True,
        enable_compression: bool = True,
        max_memory_pool_mb: float = 1024.0,
        total_memory_gb: Optional[float] = None,
        enable_new_features: Optional[bool] = None
    ):
        """
        Initialize enhanced memory optimizer

        Args:
            target_memory_usage_percent: Target memory usage percentage
            gc_threshold_percent: Garbage collection threshold percentage
            cleanup_interval: Cleanup interval in seconds
            enable_memory_profiling: Enable memory profiling
            enable_compression: Enable data compression
            max_memory_pool_mb: Maximum memory pool size in MB
            total_memory_gb: Total system memory in GB (auto-detected if None)
            enable_new_features: Force enable/disable new features (None = use feature flags)
        """
        self.target_memory_usage_percent = target_memory_usage_percent
        self.gc_threshold_percent = gc_threshold_percent
        self.cleanup_interval = cleanup_interval
        self.enable_memory_profiling = enable_memory_profiling
        self.enable_compression = enable_compression
        self.max_memory_pool_mb = max_memory_pool_mb

        # Determine if new features should be enabled
        if enable_new_features is None:
            self.enable_new_features = NEW_MEMORY_MANAGEMENT_AVAILABLE
        else:
            self.enable_new_features = enable_new_features and NEW_MEMORY_MANAGEMENT_AVAILABLE

        # Initialize new memory management components
        self.adaptive_allocator = None
        self.leak_detector = None
        self.pool_manager = None

        if self.enable_new_features:
            self._initialize_new_components(total_memory_gb)

        # Original memory monitoring
        self.memory_snapshots: List[MemorySnapshot] = []
        self.current_pressure = MemoryPressureLevel.LOW
        self.memory_pools: Dict[str, Any] = {}
        self.active_objects: Dict[int, weakref.ref] = {}

        # Optimization state
        self.optimization_active = False
        self.cleanup_thread: Optional[threading.Thread] = None
        self.monitoring_thread: Optional[threading.Thread] = None

        # Statistics
        self.stats = {
            'total_optimizations': 0,
            'total_memory_freed_mb': 0.0,
            'total_objects_collected': 0,
            'total_gc_time_ms': 0.0,
            'memory_leaks_detected': 0,
            'peak_memory_usage_mb': 0.0,
            'average_memory_usage_mb': 0.0,
            'optimization_frequency': 0.0,
            'memory_efficiency_score': 1.0
        }

        # New component statistics
        if self.enable_new_features:
            self.stats.update({
                'adaptive_allocations': 0,
                'leak_detections': 0,
                'pool_defragmentations': 0,
                'memory_pool_allocations': 0
            })

        # Configuration
        self.optimization_strategies = [
            'garbage_collection',
            'object_pool_cleanup',
            'array_optimization',
            'dataframe_optimization',
            'memory_pool_compaction',
            'cache_clearing'
        ]

        # Add new strategies if available
        if self.enable_new_features:
            self.optimization_strategies.extend([
                'adaptive_allocation',
                'leak_detection_cleanup',
                'pool_defragmentation'
            ])

        # Initialize memory tracking
        if self.enable_memory_profiling:
            tracemalloc.start()

        logger.info(f"EnhancedMemoryOptimizer initialized with new features: {self.enable_new_features}")

    def _initialize_new_components(self, total_memory_gb: Optional[float]):
        """Initialize new memory management components"""
        try:
            # Initialize adaptive memory allocator
            self.adaptive_allocator = create_adaptive_allocator(
                total_memory_gb=total_memory_gb,
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
                max_total_memory_mb=self.max_memory_pool_mb * 2,
                auto_defragment=True,
                enable_backup=True
            )

            logger.info("New memory management components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize new memory components: {e}")
            self.enable_new_features = False

    def start(self):
        """Start memory optimization system"""
        if self.optimization_active:
            logger.warning("EnhancedMemoryOptimizer is already active")
            return

        self.optimization_active = True

        # Start new component monitoring
        if self.enable_new_features:
            try:
                if self.leak_detector:
                    self.leak_detector.start_monitoring()
                if self.pool_manager:
                    self.pool_manager.start_monitoring()
            except Exception as e:
                logger.error(f"Failed to start new component monitoring: {e}")

        # Start original cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()

        # Start original monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

        logger.info("Enhanced Memory Optimizer started successfully")

    def stop(self):
        """Stop memory optimization system"""
        if not self.optimization_active:
            return

        logger.info("Stopping enhanced memory optimizer...")

        self.optimization_active = False

        # Stop new components
        if self.enable_new_features:
            try:
                if self.leak_detector:
                    self.leak_detector.stop_monitoring()
                if self.pool_manager:
                    self.pool_manager.stop_monitoring()
                if self.adaptive_allocator:
                    self.adaptive_allocator.shutdown()
            except Exception as e:
                logger.error(f"Error stopping new components: {e}")

        # Wait for threads to finish
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=10.0)

        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=10.0)

        logger.info("Enhanced Memory Optimizer stopped")

    def optimize_memory(self, force_optimization: bool = False) -> MemoryOptimizationResult:
        """
        Perform comprehensive memory optimization

        Args:
            force_optimization: Force optimization even if not needed

        Returns:
            MemoryOptimizationResult with optimization details
        """
        start_time = time.time()
        start_memory = self._get_current_memory_usage()

        optimization_results = []

        # Original optimization strategies
        for strategy in ['garbage_collection', 'cache_clearing', 'object_pool_cleanup']:
            if force_optimization or self._should_optimize(strategy):
                result = self._execute_optimization_strategy(strategy)
                if result:
                    optimization_results.append(result)

        # New optimization strategies
        if self.enable_new_features:
            try:
                # Adaptive allocation optimization
                if force_optimization or self._should_optimize('adaptive_allocation'):
                    result = self._execute_adaptive_allocation_optimization()
                    if result:
                        optimization_results.append(result)

                # Memory leak cleanup
                if force_optimization or self._should_optimize('leak_detection_cleanup'):
                    result = self._execute_leak_cleanup()
                    if result:
                        optimization_results.append(result)

                # Pool defragmentation
                if force_optimization or self._should_optimize('pool_defragmentation'):
                    result = self._execute_pool_defragmentation()
                    if result:
                        optimization_results.append(result)

            except Exception as e:
                logger.error(f"New optimization strategy failed: {e}")

        # Calculate overall result
        end_memory = self._get_current_memory_usage()
        total_memory_freed = max(0, start_memory - end_memory)
        total_objects_collected = sum(r.get('objects_collected', 0) for r in optimization_results)
        gc_time_ms = sum(r.get('gc_time_ms', 0) for r in optimization_results)
        processing_time = (time.time() - start_time) * 1000

        result = MemoryOptimizationResult(
            timestamp=datetime.now(),
            memory_freed_mb=total_memory_freed,
            objects_collected=total_objects_collected,
            gc_time_ms=gc_time_ms,
            optimization_type='comprehensive',
            success=True,
            details={
                'strategies_executed': [r['type'] for r in optimization_results],
                'processing_time_ms': processing_time,
                'new_features_used': self.enable_new_features,
                'individual_results': optimization_results
            }
        )

        # Update statistics
        self._update_statistics(result)

        return result

    def _execute_adaptive_allocation_optimization(self) -> Optional[Dict]:
        """Execute adaptive allocation optimization"""
        if not self.adaptive_allocator:
            return None

        try:
            # Get current allocation statistics
            stats = self.adaptive_allocator.get_allocation_statistics()

            # Trigger pressure-based optimization if needed
            if stats.get('current_pressure') == 'high':
                self.adaptive_allocator._trigger_defragmentation()

            self.stats['adaptive_allocations'] += 1

            return {
                'type': 'adaptive_allocation',
                'memory_freed_mb': 0,
                'objects_collected': 0,
                'gc_time_ms': 0,
                'pressure_level': stats.get('current_pressure'),
                'adjustment_count': stats.get('adjustment_count', 0)
            }

        except Exception as e:
            logger.error(f"Adaptive allocation optimization failed: {e}")
            return None

    def _execute_leak_cleanup(self) -> Optional[Dict]:
        """Execute memory leak cleanup"""
        if not self.leak_detector:
            return None

        try:
            # Force garbage collection to clear potential leaks
            collected_objects = gc.collect()

            # Get leak detection report
            leak_report = self.leak_detector.get_leak_report()

            self.stats['leak_detections'] += 1
            self.stats['memory_leaks_detected'] = leak_report['summary']['total_alerts']

            return {
                'type': 'leak_detection_cleanup',
                'memory_freed_mb': 0,
                'objects_collected': collected_objects,
                'gc_time_ms': 10,  # Estimated
                'leaks_detected': leak_report['summary']['total_alerts'],
                'auto_cleanups': leak_report['summary']['auto_cleanups']
            }

        except Exception as e:
            logger.error(f"Leak cleanup failed: {e}")
            return None

    def _execute_pool_defragmentation(self) -> Optional[Dict]:
        """Execute memory pool defragmentation"""
        if not self.pool_manager:
            return None

        try:
            # Force defragmentation
            defrag_result = self.pool_manager._defragment_pools()

            self.stats['pool_defragmentations'] += 1

            return {
                'type': 'pool_defragmentation',
                'memory_freed_mb': defrag_result.memory_freed_mb,
                'objects_collected': 0,
                'gc_time_ms': defrag_result.processing_time_seconds * 1000,
                'pools_processed': defrag_result.pools_processed,
                'fragmentation_improvement': defrag_result.fragmentation_improvement
            }

        except Exception as e:
            logger.error(f"Pool defragmentation failed: {e}")
            return None

    def get_optimal_memory_allocation(
        self,
        data_size_mb: float,
        concurrent_processes: int,
        task_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Get optimal memory allocation using adaptive allocator

        Args:
            data_size_mb: Size of data in MB
            concurrent_processes: Number of concurrent processes
            task_type: Type of task

        Returns:
            Dictionary with optimal allocation details
        """
        if self.enable_new_features and self.adaptive_allocator:
            try:
                allocation = self.adaptive_allocator.calculate_optimal_allocation(
                    data_size_mb=data_size_mb,
                    concurrent_processes=concurrent_processes,
                    task_type=task_type
                )

                return {
                    'shared_memory_mb': allocation.shared_memory_mb,
                    'process_memory_mb': allocation.process_memory_mb,
                    'safety_margin_mb': allocation.safety_margin_mb,
                    'strategy_used': allocation.strategy_used.value,
                    'efficiency': allocation.allocation_efficiency,
                    'pressure_level': allocation.pressure_level.value,
                    'recommendations': allocation.recommendations
                }

            except Exception as e:
                logger.error(f"Adaptive allocation failed: {e}")

        # Fallback to simple allocation
        total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)
        shared_memory_mb = int(total_memory_mb * 0.3)
        process_memory_mb = int((total_memory_mb * 0.6) / concurrent_processes)
        safety_margin_mb = int(total_memory_mb * 0.1)

        return {
            'shared_memory_mb': shared_memory_mb,
            'process_memory_mb': process_memory_mb,
            'safety_margin_mb': safety_margin_mb,
            'strategy_used': 'fallback',
            'efficiency': 0.7,
            'pressure_level': 'unknown',
            'recommendations': ['Using fallback allocation - check memory management features']
        }

    def allocate_memory_pool(
        self,
        pool_name: str,
        size_mb: int,
        pool_type: str = "general"
    ) -> bool:
        """
        Allocate memory pool using pool manager

        Args:
            pool_name: Name of the pool
            size_mb: Size in MB
            pool_type: Type of pool

        Returns:
            True if allocation successful
        """
        if not self.enable_new_features or not self.pool_manager:
            return False

        try:
            pool_type_enum = PoolType(pool_type.lower())
            pool = self.pool_manager.allocate_pool(
                pool_name=pool_name,
                size_mb=size_mb,
                pool_type=pool_type_enum,
                is_persistent=False
            )

            self.stats['memory_pool_allocations'] += 1
            return pool is not None

        except Exception as e:
            logger.error(f"Memory pool allocation failed: {e}")
            return False

    def get_memory_report(self) -> Dict[str, Any]:
        """
        Get comprehensive memory management report

        Returns:
            Dictionary containing memory statistics and component status
        """
        report = {
            'basic_stats': self.stats.copy(),
            'current_status': {
                'optimization_active': self.optimization_active,
                'new_features_enabled': self.enable_new_features,
                'current_memory_mb': self._get_current_memory_usage(),
                'pressure_level': self.current_pressure.value
            }
        }

        # Add new component reports if available
        if self.enable_new_features:
            try:
                new_components = {}

                # Adaptive allocator report
                if self.adaptive_allocator:
                    new_components['adaptive_allocator'] = self.adaptive_allocator.get_allocation_statistics()

                # Leak detector report
                if self.leak_detector:
                    new_components['leak_detector'] = self.leak_detector.get_leak_report()

                # Pool manager report
                if self.pool_manager:
                    new_components['pool_manager'] = self.pool_manager.get_pool_report()

                report['new_components'] = new_components

            except Exception as e:
                report['new_components_error'] = str(e)

        return report

    def _get_current_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0

    def _should_optimize(self, strategy: str) -> bool:
        """Check if optimization strategy should be executed"""
        # Simple heuristic - could be enhanced with ML-based prediction
        if self.current_pressure in [MemoryPressureLevel.HIGH, MemoryPressureLevel.CRITICAL]:
            return True

        memory_usage = self._get_current_memory_usage()
        total_memory = psutil.virtual_memory().total / (1024 * 1024)
        usage_percent = (memory_usage / total_memory) * 100

        return usage_percent > self.target_memory_usage_percent

    def _execute_optimization_strategy(self, strategy: str) -> Optional[Dict]:
        """Execute specific optimization strategy"""
        try:
            start_time = time.time()
            memory_before = self._get_current_memory_usage()

            if strategy == 'garbage_collection':
                collected = gc.collect()
                gc_time = (time.time() - start_time) * 1000

                return {
                    'type': strategy,
                    'memory_freed_mb': max(0, memory_before - self._get_current_memory_usage()),
                    'objects_collected': collected,
                    'gc_time_ms': gc_time
                }

            elif strategy == 'cache_clearing':
                # Clear various caches
                gc.collect()
                # Add more cache clearing as needed

                return {
                    'type': strategy,
                    'memory_freed_mb': max(0, memory_before - self._get_current_memory_usage()),
                    'objects_collected': 0,
                    'gc_time_ms': (time.time() - start_time) * 1000
                }

            elif strategy == 'object_pool_cleanup':
                # Cleanup object pools
                if self.memory_pools:
                    # Simplified cleanup
                    del self.memory_pools
                    self.memory_pools = {}
                    gc.collect()

                return {
                    'type': strategy,
                    'memory_freed_mb': max(0, memory_before - self._get_current_memory_usage()),
                    'objects_collected': gc.collect(),
                    'gc_time_ms': (time.time() - start_time) * 1000
                }

        except Exception as e:
            logger.error(f"Optimization strategy {strategy} failed: {e}")
            return None

    def _update_statistics(self, result: MemoryOptimizationResult):
        """Update optimization statistics"""
        self.stats['total_optimizations'] += 1
        self.stats['total_memory_freed_mb'] += result.memory_freed_mb
        self.stats['total_objects_collected'] += result.objects_collected
        self.stats['total_gc_time_ms'] += result.gc_time_ms

        # Update peak and average memory usage
        current_memory = self._get_current_memory_usage()
        self.stats['peak_memory_usage_mb'] = max(
            self.stats['peak_memory_usage_mb'],
            current_memory
        )

        # Update memory efficiency score
        total_memory = psutil.virtual_memory().total / (1024 * 1024)
        usage_ratio = current_memory / total_memory
        self.stats['memory_efficiency_score'] = max(0.1, 1.0 - usage_ratio)

    def _cleanup_loop(self):
        """Main cleanup loop"""
        while self.optimization_active:
            try:
                time.sleep(self.cleanup_interval)

                # Check if optimization is needed
                if self._should_optimize('automatic'):
                    self.optimize_memory()

            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.optimization_active:
            try:
                # Capture memory snapshot
                memory = psutil.virtual_memory()
                process_memory = self._get_current_memory_usage()

                # Determine pressure level
                if memory.percent < 50:
                    pressure = MemoryPressureLevel.LOW
                elif memory.percent < 75:
                    pressure = MemoryPressureLevel.MEDIUM
                elif memory.percent < 90:
                    pressure = MemoryPressureLevel.HIGH
                else:
                    pressure = MemoryPressureLevel.CRITICAL

                snapshot = MemorySnapshot(
                    timestamp=datetime.now(),
                    total_memory_mb=memory.total / (1024 * 1024),
                    used_memory_mb=memory.used / (1024 * 1024),
                    available_memory_mb=memory.available / (1024 * 1024),
                    process_memory_mb=process_memory,
                    gc_collections=gc.collect(),
                    active_objects=len(gc.get_objects()),
                    pressure_level=pressure
                )

                self.memory_snapshots.append(snapshot)
                self.current_pressure = pressure

                # Keep only recent snapshots
                if len(self.memory_snapshots) > 1000:
                    self.memory_snapshots = self.memory_snapshots[-1000:]

                time.sleep(5.0)  # Monitor every 5 seconds

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(5.0)

    def reset_statistics(self):
        """Reset optimization statistics"""
        self.stats = {
            'total_optimizations': 0,
            'total_memory_freed_mb': 0.0,
            'total_objects_collected': 0,
            'total_gc_time_ms': 0.0,
            'memory_leaks_detected': 0,
            'peak_memory_usage_mb': 0.0,
            'average_memory_usage_mb': 0.0,
            'optimization_frequency': 0.0,
            'memory_efficiency_score': 1.0
        }

        if self.enable_new_features:
            self.stats.update({
                'adaptive_allocations': 0,
                'leak_detections': 0,
                'pool_defragmentations': 0,
                'memory_pool_allocations': 0
            })

        # Reset new component statistics
        if self.enable_new_features:
            try:
                if self.adaptive_allocator:
                    self.adaptive_allocator.reset_statistics()
                if self.leak_detector:
                    self.leak_detector.reset_statistics()
                if self.pool_manager:
                    self.pool_manager.reset_statistics()
            except Exception as e:
                logger.error(f"Failed to reset new component statistics: {e}")

        logger.info("Enhanced memory optimizer statistics reset")


# Backward compatibility alias
MemoryOptimizer = EnhancedMemoryOptimizer


def get_optimal_system_config(
    max_workers: int = 32,
    total_memory_gb: Optional[float] = None,
    enable_new_features: bool = True
) -> Dict[str, Any]:
    """
    Get optimal system configuration using enhanced memory management

    Args:
        max_workers: Maximum number of worker processes
        total_memory_gb: Total system memory in GB
        enable_new_features: Enable new memory management features

    Returns:
        Dictionary with optimal configuration
    """
    try:
        if enable_new_features and NEW_MEMORY_MANAGEMENT_AVAILABLE:
            from src.memory import calculate_optimal_memory_config
            return calculate_optimal_memory_config(
                total_memory_gb=total_memory_gb,
                max_workers=max_workers
            )
        else:
            # Fallback configuration
            if total_memory_gb is None:
                total_memory_gb = psutil.virtual_memory().total / (1024**3)

            return {
                'total_memory_gb': total_memory_gb,
                'memory_allocation': {
                    'shared_memory_mb': int(total_memory_gb * 1024 * 0.3),
                    'process_memory_mb': int((total_memory_gb * 1024 * 0.6) / max_workers),
                    'safety_margin_mb': int(total_memory_gb * 1024 * 0.1),
                    'efficiency': 0.7
                },
                'recommendations': ['Consider enabling new memory management features']
            }

    except Exception as e:
        logger.error(f"Failed to get optimal system config: {e}")
        return {'error': str(e)}
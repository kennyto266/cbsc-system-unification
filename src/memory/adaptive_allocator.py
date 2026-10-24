#!/usr/bin/env python3
"""
Adaptive Memory Allocator for 32-Core Parallel Processing System
Production-grade intelligent memory allocation with dynamic adjustment

This module implements the core memory management component that addresses
the hardcoded allocation issues identified in the stability analysis.

Key Features:
- Dynamic memory allocation based on data size and system load
- Pressure-responsive allocation strategies
- Multi-process memory coordination
- Real-time memory usage monitoring
- Automatic memory pool adjustment
- Production-grade error handling and logging
"""

import os
import sys
import gc
import time
import threading
import logging
import psutil
import numpy as np
import multiprocessing as mp
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import weakref
import json
from contextlib import contextmanager

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


class MemoryPressureLevel(Enum):
    """Memory pressure levels for adaptive allocation"""
    LOW = "low"          # < 50% memory usage
    MEDIUM = "medium"    # 50-75% memory usage
    HIGH = "high"        # 75-85% memory usage
    CRITICAL = "critical" # > 85% memory usage


class AllocationStrategy(Enum):
    """Memory allocation strategies"""
    CONSERVATIVE = "conservative"  # prioritize memory safety
    BALANCED = "balanced"         # balance between speed and memory
    AGGRESSIVE = "aggressive"     # prioritize processing speed
    ADAPTIVE = "adaptive"         # dynamically adjust based on pressure


@dataclass
class MemoryAllocationResult:
    """Result of memory allocation calculation"""
    timestamp: datetime
    total_memory_gb: float
    shared_memory_mb: int
    process_memory_mb: int
    safety_margin_mb: int
    strategy_used: AllocationStrategy
    pressure_level: MemoryPressureLevel
    data_pressure_ratio: float
    concurrent_processes: int
    allocation_efficiency: float
    recommendations: List[str] = field(default_factory=list)


@dataclass
class SystemMemoryState:
    """Current system memory state"""
    timestamp: datetime
    total_memory_gb: float
    available_memory_gb: float
    used_memory_gb: float
    usage_percent: float
    pressure_level: MemoryPressureLevel
    active_processes: int
    gc_collections: int
    fragmentation_estimate: float


class AdaptiveMemoryAllocator:
    """
    Adaptive Memory Allocator for High-Performance Parallel Processing

    This class replaces the hardcoded memory allocation strategy with an
    intelligent, data-driven approach that adapts to system conditions.

    Key Improvements over Original Implementation:
    - Eliminates hardcoded 50% shared memory allocation
    - Dynamic adjustment based on data size and concurrent processes
    - Pressure-responsive allocation strategies
    - Real-time monitoring and automatic adjustment
    - Production-grade error handling and recovery
    """

    def __init__(
        self,
        total_memory_gb: float,
        enable_monitoring: bool = True,
        monitoring_interval: float = 5.0,
        safety_margin_percent: float = 10.0,
        enable_fragmentation_tracking: bool = True,
        log_allocations: bool = False
    ):
        """
        Initialize the adaptive memory allocator

        Args:
            total_memory_gb: Total system memory in GB
            enable_monitoring: Enable real-time memory monitoring
            monitoring_interval: Memory monitoring interval in seconds
            safety_margin_percent: Safety margin percentage for allocations
            enable_fragmentation_tracking: Enable memory fragmentation tracking
            log_allocations: Log all allocation decisions for debugging
        """
        self.total_memory_gb = total_memory_gb
        self.enable_monitoring = enable_monitoring
        self.monitoring_interval = monitoring_interval
        self.safety_margin_percent = safety_margin_percent
        self.enable_fragmentation_tracking = enable_fragmentation_tracking
        self.log_allocations = log_allocations

        # Dynamic allocation parameters
        self.shared_memory_ratio = 0.3  # Initial 30% for shared memory
        self.pressure_threshold = 0.8   # 80% pressure threshold
        self.current_strategy = AllocationStrategy.ADAPTIVE

        # System state tracking
        self.allocation_history: List[MemoryAllocationResult] = []
        self.memory_snapshots: List[SystemMemoryState] = []
        self.current_pressure = MemoryPressureLevel.LOW
        self.allocation_lock = threading.Lock()

        # Performance metrics
        self.total_allocations = 0
        self.adjustment_count = 0
        self.oom_prevention_count = 0

        # Fragmentation tracking
        self.fragmentation_history: List[float] = []
        self.last_defragmentation = None

        # Feature flag integration
        self.feature_enabled = self._check_feature_flag()

        # Start monitoring thread if enabled
        self.monitoring_active = False
        self.monitor_thread = None

        if self.enable_monitoring and self.feature_enabled:
            self._start_monitoring()

        logger.info(f"AdaptiveMemoryAllocator initialized: {total_memory_gb}GB total memory")

    def _check_feature_flag(self) -> bool:
        """Check if adaptive memory allocation feature is enabled"""
        try:
            # Check for feature flag configuration
            feature_config_path = Path(__file__).parent.parent / "config" / "feature_flags.yaml"
            if feature_config_path.exists():
                import yaml
                with open(feature_config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    return config.get('feature_flags', {}).get('enable_adaptive_memory', False)

            # Default to False for safe rollout
            return False

        except Exception as e:
            logger.warning(f"Could not check feature flag: {e}")
            return False

    def _start_monitoring(self):
        """Start memory monitoring thread"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            name="MemoryAllocatorMonitor",
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("Memory allocator monitoring started")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Capture current system state
                memory_state = self._capture_system_state()

                # Update pressure level
                self._update_pressure_level(memory_state)

                # Adjust allocation strategy if needed
                self._adjust_strategy_if_needed(memory_state)

                # Track fragmentation if enabled
                if self.enable_fragmentation_tracking:
                    self._track_fragmentation(memory_state)

                # Clean up old snapshots
                self._cleanup_old_snapshots()

                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
                time.sleep(self.monitoring_interval)

    def _capture_system_state(self) -> SystemMemoryState:
        """Capture current system memory state"""
        try:
            memory = psutil.virtual_memory()
            process = psutil.Process()

            # Estimate fragmentation
            fragmentation = self._estimate_fragmentation()

            state = SystemMemoryState(
                timestamp=datetime.now(),
                total_memory_gb=memory.total / (1024**3),
                available_memory_gb=memory.available / (1024**3),
                used_memory_gb=memory.used / (1024**3),
                usage_percent=memory.percent,
                pressure_level=self.current_pressure,
                active_processes=len(psutil.pids()),
                gc_collections=gc.collect(),
                fragmentation_estimate=fragmentation
            )

            self.memory_snapshots.append(state)
            return state

        except Exception as e:
            logger.error(f"Failed to capture system state: {e}")
            # Return safe defaults
            return SystemMemoryState(
                timestamp=datetime.now(),
                total_memory_gb=self.total_memory_gb,
                available_memory_gb=self.total_memory_gb * 0.5,
                used_memory_gb=self.total_memory_gb * 0.5,
                usage_percent=50.0,
                pressure_level=MemoryPressureLevel.MEDIUM,
                active_processes=1,
                gc_collections=0,
                fragmentation_estimate=0.1
            )

    def _estimate_fragmentation(self) -> float:
        """Estimate memory fragmentation level"""
        try:
            # Use object counts and memory distribution as fragmentation proxy
            import tracemalloc

            if not tracemalloc.is_tracing():
                tracemalloc.start()

            # Get current memory statistics
            current, peak = tracemalloc.get_traced_memory()

            # Simple fragmentation estimate based on memory distribution
            # This is a simplified metric - in production, you'd use more sophisticated methods
            fragmentation = min(0.5, (peak - current) / (1024**3) if peak > 0 else 0)

            return fragmentation

        except Exception:
            # Fallback estimation
            return 0.1  # 10% assumed fragmentation

    def _update_pressure_level(self, memory_state: SystemMemoryState):
        """Update memory pressure level based on current state"""
        old_pressure = self.current_pressure

        if memory_state.usage_percent < 50:
            self.current_pressure = MemoryPressureLevel.LOW
        elif memory_state.usage_percent < 75:
            self.current_pressure = MemoryPressureLevel.MEDIUM
        elif memory_state.usage_percent < 85:
            self.current_pressure = MemoryPressureLevel.HIGH
        else:
            self.current_pressure = MemoryPressureLevel.CRITICAL

        # Log pressure level changes
        if old_pressure != self.current_pressure:
            logger.info(f"Memory pressure changed: {old_pressure.value} -> {self.current_pressure.value}")

    def _adjust_strategy_if_needed(self, memory_state: SystemMemoryState):
        """Adjust allocation strategy based on memory pressure"""
        old_strategy = self.current_strategy

        if self.current_pressure == MemoryPressureLevel.CRITICAL:
            self.current_strategy = AllocationStrategy.CONSERVATIVE
            self.shared_memory_ratio = min(0.2, self.shared_memory_ratio - 0.1)
        elif self.current_pressure == MemoryPressureLevel.HIGH:
            self.current_strategy = AllocationStrategy.BALANCED
            self.shared_memory_ratio = min(0.4, max(0.2, self.shared_memory_ratio))
        elif self.current_pressure == MemoryPressureLevel.MEDIUM:
            self.current_strategy = AllocationStrategy.ADAPTIVE
            self.shared_memory_ratio = min(0.5, max(0.3, self.shared_memory_ratio))
        else:  # LOW pressure
            self.current_strategy = AllocationStrategy.AGGRESSIVE
            self.shared_memory_ratio = min(0.6, self.shared_memory_ratio + 0.05)

        if old_strategy != self.current_strategy:
            self.adjustment_count += 1
            logger.info(f"Allocation strategy adjusted: {old_strategy.value} -> {self.current_strategy.value}")

    def _track_fragmentation(self, memory_state: SystemMemoryState):
        """Track memory fragmentation over time"""
        self.fragmentation_history.append(memory_state.fragmentation_estimate)

        # Keep only recent history
        if len(self.fragmentation_history) > 100:
            self.fragmentation_history = self.fragmentation_history[-100:]

        # Trigger defragmentation if needed
        if memory_state.fragmentation_estimate > 0.3:  # 30% fragmentation threshold
            self._trigger_defragmentation()

    def _trigger_defragmentation(self):
        """Trigger memory defragmentation"""
        try:
            logger.info("Triggering memory defragmentation")

            # Force garbage collection
            collected = gc.collect()

            # Compact memory pools if possible
            self._compact_memory_pools()

            self.last_defragmentation = datetime.now()
            logger.info(f"Memory defragmentation completed: {collected} objects collected")

        except Exception as e:
            logger.error(f"Memory defragmentation failed: {e}")

    def _compact_memory_pools(self):
        """Compact memory pools to reduce fragmentation"""
        # This would integrate with the memory pool manager
        # For now, just trigger Python's garbage collection more aggressively
        for _ in range(3):
            gc.collect()

    def _cleanup_old_snapshots(self):
        """Clean up old memory snapshots to prevent memory leaks"""
        max_snapshots = 1000
        if len(self.memory_snapshots) > max_snapshots:
            self.memory_snapshots = self.memory_snapshots[-max_snapshots:]

        max_allocations = 500
        if len(self.allocation_history) > max_allocations:
            self.allocation_history = self.allocation_history[-max_allocations:]

    def calculate_optimal_allocation(
        self,
        data_size_mb: float,
        concurrent_processes: int,
        task_type: str = "general",
        priority_level: str = "normal"
    ) -> MemoryAllocationResult:
        """
        Calculate optimal memory allocation for given parameters

        This method replaces the hardcoded allocation with intelligent
        calculation based on data size, system pressure, and concurrent load.

        Args:
            data_size_mb: Size of data to be processed in MB
            concurrent_processes: Number of concurrent processes
            task_type: Type of task (general, backtesting, optimization, etc.)
            priority_level: Priority level of the task

        Returns:
            MemoryAllocationResult with allocation details
        """
        with self.allocation_lock:
            try:
                # Get current system state
                memory_state = self._capture_system_state()

                # Calculate data pressure ratio
                total_memory_mb = self.total_memory_gb * 1024
                data_pressure = data_size_mb / total_memory_mb

                # Adjust shared memory ratio based on multiple factors
                self._adjust_shared_memory_ratio(data_pressure, concurrent_processes, task_type)

                # Calculate memory allocations
                shared_memory_mb = int(total_memory_mb * self.shared_memory_ratio)
                process_memory_total = total_memory_mb - shared_memory_mb
                process_memory_mb = int(process_memory_total / concurrent_processes)
                safety_margin_mb = int(total_memory_mb * self.safety_margin_percent / 100)

                # Apply safety checks
                final_allocation = self._apply_safety_checks(
                    shared_memory_mb, process_memory_mb, safety_margin_mb, memory_state
                )

                # Calculate allocation efficiency
                total_allocated = sum(final_allocation.values())
                allocation_efficiency = min(1.0, (data_size_mb + safety_margin_mb) / total_allocated)

                # Generate recommendations
                recommendations = self._generate_recommendations(
                    data_pressure, memory_state, final_allocation
                )

                # Create result
                result = MemoryAllocationResult(
                    timestamp=datetime.now(),
                    total_memory_gb=self.total_memory_gb,
                    shared_memory_mb=final_allocation['shared_memory_mb'],
                    process_memory_mb=final_allocation['process_memory_mb'],
                    safety_margin_mb=final_allocation['safety_margin_mb'],
                    strategy_used=self.current_strategy,
                    pressure_level=self.current_pressure,
                    data_pressure_ratio=data_pressure,
                    concurrent_processes=concurrent_processes,
                    allocation_efficiency=allocation_efficiency,
                    recommendations=recommendations
                )

                # Log allocation if enabled
                if self.log_allocations:
                    logger.info(f"Memory allocation: {result}")

                # Store in history
                self.allocation_history.append(result)
                self.total_allocations += 1

                return result

            except Exception as e:
                logger.error(f"Failed to calculate memory allocation: {e}")
                # Return safe fallback allocation
                return self._get_fallback_allocation(data_size_mb, concurrent_processes)

    def _adjust_shared_memory_ratio(
        self,
        data_pressure: float,
        concurrent_processes: int,
        task_type: str
    ):
        """Adjust shared memory ratio based on input parameters"""
        # Data pressure adjustment
        if data_pressure > 0.5:
            # High data pressure - allocate more to shared memory for efficiency
            target_ratio = min(0.6, 0.3 + data_pressure * 0.3)
        elif data_pressure < 0.1:
            # Low data pressure - allocate more to processes
            target_ratio = max(0.2, 0.3 - data_pressure * 0.2)
        else:
            # Normal pressure - balanced allocation
            target_ratio = 0.3

        # Process count adjustment
        if concurrent_processes > 24:  # 32-core system with high concurrency
            target_ratio *= 1.1  # More shared memory for coordination
        elif concurrent_processes < 8:
            target_ratio *= 0.8  # Less need for shared memory

        # Task type adjustment
        if task_type == "backtesting":
            target_ratio *= 1.2  # Backtesting benefits from shared data
        elif task_type == "optimization":
            target_ratio *= 1.1  # Optimization needs parameter sharing
        elif task_type == "data_processing":
            target_ratio *= 0.9  # More individual memory for processing

        # Apply strategy-based adjustments
        if self.current_strategy == AllocationStrategy.CONSERVATIVE:
            target_ratio *= 0.8
        elif self.current_strategy == AllocationStrategy.AGGRESSIVE:
            target_ratio *= 1.2

        # Ensure within reasonable bounds
        self.shared_memory_ratio = max(0.15, min(0.65, target_ratio))

    def _apply_safety_checks(
        self,
        shared_memory_mb: int,
        process_memory_mb: int,
        safety_margin_mb: int,
        memory_state: SystemMemoryState
    ) -> Dict[str, int]:
        """Apply safety checks to prevent OOM"""
        available_mb = memory_state.available_memory_gb * 1024
        total_requested = shared_memory_mb + (process_memory_mb * 32) + safety_margin_mb

        # If we're requesting more than available memory, scale down
        if total_requested > available_mb * 0.9:  # Leave 10% buffer
            scale_factor = (available_mb * 0.9) / total_requested
            logger.warning(f"Scaling down allocation by {scale_factor:.2f} due to memory constraints")

            shared_memory_mb = int(shared_memory_mb * scale_factor)
            process_memory_mb = int(process_memory_mb * scale_factor)
            safety_margin_mb = int(safety_margin_mb * scale_factor)
            self.oom_prevention_count += 1

        # Ensure minimum allocations
        shared_memory_mb = max(512, shared_memory_mb)  # At least 512MB for shared memory
        process_memory_mb = max(256, process_memory_mb)  # At least 256MB per process
        safety_margin_mb = max(512, safety_margin_mb)  # At least 512MB safety margin

        return {
            'shared_memory_mb': shared_memory_mb,
            'process_memory_mb': process_memory_mb,
            'safety_margin_mb': safety_margin_mb
        }

    def _generate_recommendations(
        self,
        data_pressure: float,
        memory_state: SystemMemoryState,
        allocation: Dict[str, int]
    ) -> List[str]:
        """Generate recommendations based on allocation analysis"""
        recommendations = []

        # Data pressure recommendations
        if data_pressure > 0.7:
            recommendations.append("Consider processing data in smaller chunks")
            recommendations.append("Enable data compression to reduce memory footprint")
        elif data_pressure < 0.1:
            recommendations.append("Memory usage is low - consider increasing batch size")

        # Memory pressure recommendations
        if memory_state.pressure_level == MemoryPressureLevel.CRITICAL:
            recommendations.append("Critical memory pressure - consider reducing concurrent processes")
            recommendations.append("Immediate garbage collection recommended")
        elif memory_state.pressure_level == MemoryPressureLevel.HIGH:
            recommendations.append("High memory pressure - monitor closely")

        # Efficiency recommendations
        total_allocated = sum(allocation.values())
        if total_allocated < (memory_state.available_memory_gb * 1024 * 0.5):
            recommendations.append("Under-utilizing available memory - allocation could be more aggressive")

        # Fragmentation recommendations
        if memory_state.fragmentation_estimate > 0.3:
            recommendations.append("High memory fragmentation detected - consider memory compaction")

        return recommendations

    def _get_fallback_allocation(
        self,
        data_size_mb: float,
        concurrent_processes: int
    ) -> MemoryAllocationResult:
        """Get safe fallback allocation if calculation fails"""
        total_memory_mb = self.total_memory_gb * 1024

        # Conservative fallback allocation
        shared_memory_mb = int(total_memory_mb * 0.25)  # 25% shared memory
        process_memory_mb = max(512, int((total_memory_mb * 0.6) / concurrent_processes))  # 60% for processes
        safety_margin_mb = int(total_memory_mb * 0.15)  # 15% safety margin

        return MemoryAllocationResult(
            timestamp=datetime.now(),
            total_memory_gb=self.total_memory_gb,
            shared_memory_mb=shared_memory_mb,
            process_memory_mb=process_memory_mb,
            safety_margin_mb=safety_margin_mb,
            strategy_used=AllocationStrategy.CONSERVATIVE,
            pressure_level=MemoryPressureLevel.MEDIUM,
            data_pressure_ratio=data_size_mb / total_memory_mb,
            concurrent_processes=concurrent_processes,
            allocation_efficiency=0.7,
            recommendations=["Fallback allocation used - check system resources"]
        )

    def get_allocation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive allocation statistics"""
        if not self.allocation_history:
            return {"error": "No allocation history available"}

        recent_allocations = self.allocation_history[-100:]  # Last 100 allocations

        avg_shared_memory = np.mean([a.shared_memory_mb for a in recent_allocations])
        avg_process_memory = np.mean([a.process_memory_mb for a in recent_allocations])
        avg_efficiency = np.mean([a.allocation_efficiency for a in recent_allocations])

        strategy_counts = {}
        for allocation in recent_allocations:
            strategy = allocation.strategy_used.value
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        return {
            'total_allocations': self.total_allocations,
            'adjustment_count': self.adjustment_count,
            'oom_prevention_count': self.oom_prevention_count,
            'current_strategy': self.current_strategy.value,
            'current_pressure': self.current_pressure.value,
            'shared_memory_ratio': self.shared_memory_ratio,
            'recent_stats': {
                'avg_shared_memory_mb': avg_shared_memory,
                'avg_process_memory_mb': avg_process_memory,
                'avg_efficiency': avg_efficiency,
                'strategy_distribution': strategy_counts
            },
            'fragmentation': {
                'current_estimate': self.fragmentation_history[-1] if self.fragmentation_history else 0,
                'last_defragmentation': self.last_defragmentation.isoformat() if self.last_defragmentation else None
            }
        }

    def reset_statistics(self):
        """Reset allocation statistics"""
        self.total_allocations = 0
        self.adjustment_count = 0
        self.oom_prevention_count = 0
        self.allocation_history.clear()
        self.memory_snapshots.clear()
        self.fragmentation_history.clear()
        logger.info("Memory allocator statistics reset")

    def shutdown(self):
        """Shutdown the memory allocator"""
        self.monitoring_active = False

        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)

        logger.info("AdaptiveMemoryAllocator shutdown complete")

    @contextmanager
    def temporary_allocation(self, data_size_mb: float, concurrent_processes: int = 1):
        """Context manager for temporary memory allocation"""
        allocation = self.calculate_optimal_allocation(data_size_mb, concurrent_processes)

        try:
            logger.debug(f"Temporary allocation: {allocation.shared_memory_mb}MB shared, "
                        f"{allocation.process_memory_mb}MB per process")
            yield allocation
        finally:
            # Clean up any temporary memory
            gc.collect()
            logger.debug("Temporary allocation cleaned up")


# Factory function for easy instantiation
def create_adaptive_allocator(
    total_memory_gb: Optional[float] = None,
    **kwargs
) -> AdaptiveMemoryAllocator:
    """
    Factory function to create adaptive memory allocator

    Args:
        total_memory_gb: Total system memory in GB (auto-detected if None)
        **kwargs: Additional arguments for AdaptiveMemoryAllocator

    Returns:
        AdaptiveMemoryAllocator instance
    """
    if total_memory_gb is None:
        # Auto-detect system memory
        memory = psutil.virtual_memory()
        total_memory_gb = memory.total / (1024**3)
        logger.info(f"Auto-detected system memory: {total_memory_gb:.1f}GB")

    return AdaptiveMemoryAllocator(total_memory_gb=total_memory_gb, **kwargs)


# Utility function for quick allocation calculation
def calculate_memory_allocation(
    data_size_mb: float,
    concurrent_processes: int = 32,
    total_memory_gb: Optional[float] = None
) -> Dict[str, int]:
    """
    Quick utility function to calculate memory allocation

    Args:
        data_size_mb: Size of data in MB
        concurrent_processes: Number of concurrent processes
        total_memory_gb: Total system memory in GB (auto-detected if None)

    Returns:
        Dictionary with memory allocation details
    """
    allocator = create_adaptive_allocator(total_memory_gb)
    result = allocator.calculate_optimal_allocation(data_size_mb, concurrent_processes)

    return {
        'shared_memory_mb': result.shared_memory_mb,
        'process_memory_mb': result.process_memory_mb,
        'safety_margin_mb': result.safety_margin_mb,
        'efficiency': result.allocation_efficiency
    }
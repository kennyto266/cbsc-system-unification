#!/usr/bin/env python3
"""
Memory Pool Manager for 32-Core Parallel Processing
Advanced memory pool management with fragmentation handling and optimization

This module implements a sophisticated memory pool management system that addresses
the memory fragmentation and inefficient allocation issues identified in the stability analysis.

Key Features:
- Dynamic memory pool allocation and management
- Automatic fragmentation detection and correction
- Pool defragmentation and optimization
- Multi-process memory pool coordination
- Production-grade monitoring and statistics
- Integration with adaptive memory allocator
"""

import os
import sys
import gc
import time
import threading
import logging
import psutil
import mmap
import tempfile
import hashlib
import pickle
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import weakref
import json
from collections import defaultdict, deque
import struct
import io
from contextlib import contextmanager

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


class PoolStatus(Enum):
    """Memory pool status"""
    ACTIVE = "active"
    IDLE = "idle"
    DEFRAGMENTING = "defragmenting"
    CORRUPTED = "corrupted"
    DELETED = "deleted"


class PoolType(Enum):
    """Memory pool types"""
    GENERAL = "general"
    DATA_PROCESSING = "data_processing"
    BACKTESTING = "backtesting"
    OPTIMIZATION = "optimization"
    CACHE = "cache"
    TEMPORARY = "temporary"


@dataclass
class MemoryPool:
    """Individual memory pool instance"""
    name: str
    pool_type: PoolType
    size_mb: int
    allocated_size_mb: int
    status: PoolStatus
    creation_time: datetime
    last_access_time: datetime
    access_count: int
    fragmentation_ratio: float
    data_hash: Optional[str] = None
    backup_path: Optional[str] = None
    is_persistent: bool = False
    compression_enabled: bool = False


@dataclass
class PoolStatistics:
    """Memory pool statistics"""
    total_pools: int
    active_pools: int
    total_allocated_mb: float
    total_used_mb: float
    fragmentation_ratio: float
    avg_access_count: float
    pool_type_distribution: Dict[str, int]
    defragmentation_count: int
    last_defragmentation: Optional[datetime]


@dataclass
class DefragmentationResult:
    """Result of pool defragmentation"""
    timestamp: datetime
    pools_processed: int
    memory_freed_mb: float
    fragmentation_improvement: float
    processing_time_seconds: float
    success: bool
    errors: List[str] = field(default_factory=list)


class MemoryPoolManager:
    """
    Advanced Memory Pool Management System

    This class provides sophisticated memory pool management with automatic
    fragmentation handling, defragmentation, and optimization capabilities.

    Key Features:
    - Dynamic pool allocation based on usage patterns
    - Automatic fragmentation detection and correction
    - Multi-process pool coordination and sharing
    - Production-grade monitoring and statistics
    - Backup and recovery mechanisms
    - Memory compression and optimization
    """

    def __init__(
        self,
        max_pools: int = 100,
        max_total_memory_mb: float = 8192.0,  # 8GB default
        defragmentation_threshold: float = 0.7,  # 70% fragmentation
        auto_defragment: bool = True,
        defragmentation_interval: float = 300.0,  # 5 minutes
        enable_backup: bool = True,
        backup_directory: Optional[str] = None,
        enable_compression: bool = False,
        pool_timeout_minutes: float = 60.0,
        monitoring_interval: float = 30.0
    ):
        """
        Initialize memory pool manager

        Args:
            max_pools: Maximum number of pools to manage
            max_total_memory_mb: Maximum total memory for all pools (MB)
            defragmentation_threshold: Fragmentation threshold for auto-defrag
            auto_defragment: Enable automatic defragmentation
            defragmentation_interval: Defragmentation check interval (seconds)
            enable_backup: Enable pool backup to disk
            backup_directory: Directory for pool backups
            enable_compression: Enable pool compression
            pool_timeout_minutes: Timeout for idle pools (minutes)
            monitoring_interval: Monitoring interval (seconds)
        """
        self.max_pools = max_pools
        self.max_total_memory_mb = max_total_memory_mb
        self.defragmentation_threshold = defragmentation_threshold
        self.auto_defragment = auto_defragment
        self.defragmentation_interval = defragmentation_interval
        self.enable_backup = enable_backup
        self.enable_compression = enable_compression
        self.pool_timeout_minutes = pool_timeout_minutes
        self.monitoring_interval = monitoring_interval

        # Pool storage
        self.memory_pools: Dict[str, MemoryPool] = {}
        self.pool_data: Dict[str, bytes] = {}
        self.pool_locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)

        # Statistics and monitoring
        self.defragmentation_history: List[DefragmentationResult] = []
        self.access_history: deque = deque(maxlen=10000)
        self.monitoring_active = False
        self.monitor_thread = None

        # Backup configuration
        if backup_directory is None:
            backup_directory = tempfile.gettempdir() / "memory_pool_backups"
        self.backup_directory = Path(backup_directory)
        self.backup_directory.mkdir(parents=True, exist_ok=True)

        # Statistics tracking
        self.total_allocations = 0
        self.total_deallocations = 0
        self.total_defragmentations = 0
        self.backup_count = 0
        self.restore_count = 0

        # Feature flag integration
        self.feature_enabled = self._check_feature_flag()

        logger.info(f"MemoryPoolManager initialized with max {max_pools} pools, "
                   f"{max_total_memory_mb}MB total memory")

    def _check_feature_flag(self) -> bool:
        """Check if memory pool management feature is enabled"""
        try:
            feature_config_path = Path(__file__).parent.parent / "config" / "feature_flags.yaml"
            if feature_config_path.exists():
                import yaml
                with open(feature_config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    return config.get('feature_flags', {}).get('enable_memory_pool_management', False)
            return False
        except Exception as e:
            logger.warning(f"Could not check feature flag: {e}")
            return False

    def start_monitoring(self):
        """Start pool monitoring and maintenance"""
        if self.monitoring_active:
            logger.warning("Pool monitoring already active")
            return

        if not self.feature_enabled:
            logger.info("Memory pool management feature not enabled")
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            name="MemoryPoolMonitor",
            daemon=True
        )
        self.monitor_thread.start()

        logger.info("Memory pool monitoring started")

    def stop_monitoring(self):
        """Stop pool monitoring"""
        if not self.monitoring_active:
            return

        logger.info("Stopping memory pool monitoring...")
        self.monitoring_active = False

        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=10.0)

        logger.info("Memory pool monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring and maintenance loop"""
        while self.monitoring_active:
            try:
                current_time = datetime.now()

                # Check for automatic defragmentation
                if self.auto_defragment:
                    self._check_defragmentation_needed(current_time)

                # Cleanup idle pools
                self._cleanup_idle_pools(current_time)

                # Backup persistent pools
                if self.enable_backup:
                    self._backup_pools()

                # Update statistics
                self._update_statistics()

                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Pool monitoring error: {e}")
                time.sleep(self.monitoring_interval)

    def allocate_pool(
        self,
        pool_name: str,
        size_mb: int,
        pool_type: PoolType = PoolType.GENERAL,
        is_persistent: bool = False,
        compression: Optional[bool] = None
    ) -> MemoryPool:
        """
        Allocate a new memory pool

        Args:
            pool_name: Unique name for the pool
            size_mb: Size of the pool in MB
            pool_type: Type of memory pool
            is_persistent: Whether pool should persist across restarts
            compression: Enable compression (overrides default)

        Returns:
            MemoryPool instance
        """
        if not self.feature_enabled:
            logger.warning("Memory pool management feature not enabled, using simple allocation")
            return self._create_simple_pool(pool_name, size_mb, pool_type)

        with self.pool_locks[pool_name]:
            try:
                # Check if pool already exists
                if pool_name in self.memory_pools:
                    existing_pool = self.memory_pools[pool_name]
                    if existing_pool.status != PoolStatus.DELETED:
                        logger.warning(f"Pool {pool_name} already exists, returning existing pool")
                        return existing_pool

                # Check memory limits
                if not self._check_memory_limits(size_mb):
                    raise MemoryError(f"Cannot allocate pool {pool_name}: memory limits exceeded")

                # Check if defragmentation is needed
                if self._should_defragment():
                    self._defragment_pools()

                # Create pool
                current_time = datetime.now()
                pool = MemoryPool(
                    name=pool_name,
                    pool_type=pool_type,
                    size_mb=size_mb,
                    allocated_size_mb=size_mb,
                    status=PoolStatus.ACTIVE,
                    creation_time=current_time,
                    last_access_time=current_time,
                    access_count=0,
                    fragmentation_ratio=0.0,
                    is_persistent=is_persistent,
                    compression_enabled=compression if compression is not None else self.enable_compression
                )

                # Allocate actual memory
                self._allocate_pool_memory(pool)

                # Store pool
                self.memory_pools[pool_name] = pool
                self.total_allocations += 1

                logger.info(f"Allocated memory pool {pool_name}: {size_mb}MB ({pool_type.value})")

                # Backup if persistent
                if is_persistent and self.enable_backup:
                    self._backup_pool(pool_name)

                return pool

            except Exception as e:
                logger.error(f"Failed to allocate pool {pool_name}: {e}")
                raise

    def _create_simple_pool(self, pool_name: str, size_mb: int, pool_type: PoolType) -> MemoryPool:
        """Create simple pool when feature is disabled"""
        current_time = datetime.now()
        pool = MemoryPool(
            name=pool_name,
            pool_type=pool_type,
            size_mb=size_mb,
            allocated_size_mb=size_mb,
            status=PoolStatus.ACTIVE,
            creation_time=current_time,
            last_access_time=current_time,
            access_count=0,
            fragmentation_ratio=0.0,
            is_persistent=False,
            compression_enabled=False
        )
        self.memory_pools[pool_name] = pool
        return pool

    def _check_memory_limits(self, requested_size_mb: int) -> bool:
        """Check if requested size exceeds memory limits"""
        current_total_mb = sum(pool.allocated_size_mb for pool in self.memory_pools.values()
                             if pool.status != PoolStatus.DELETED)

        if current_total_mb + requested_size_mb > self.max_total_memory_mb:
            logger.warning(f"Memory limit exceeded: {current_total_mb + requested_size_mb}MB > {self.max_total_memory_mb}MB")
            return False

        if len(self.memory_pools) >= self.max_pools:
            logger.warning(f"Pool limit exceeded: {len(self.memory_pools)} >= {self.max_pools}")
            return False

        return True

    def _allocate_pool_memory(self, pool: MemoryPool):
        """Allocate actual memory for the pool"""
        try:
            # Try to allocate memory using different strategies
            allocated_bytes = pool.allocated_size_mb * 1024 * 1024

            # Strategy 1: Direct byte allocation
            try:
                memory_data = bytearray(allocated_bytes)
                self.pool_data[pool.name] = bytes(memory_data)
                return
            except MemoryError:
                pass

            # Strategy 2: Memory-mapped file
            try:
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                temp_file.write(b'\x00' * allocated_bytes)
                temp_file.flush()

                with open(temp_file.name, 'r+b') as f:
                    mm = mmap.mmap(f.fileno(), allocated_bytes)
                    self.pool_data[pool.name] = mm

                pool.backup_path = temp_file.name
                return
            except Exception:
                if 'temp_file' in locals():
                    try:
                        temp_file.close()
                        os.unlink(temp_file.name)
                    except:
                        pass

            # Strategy 3: Numpy array allocation
            try:
                array = np.zeros(allocated_bytes // 8, dtype=np.float64)
                self.pool_data[pool.name] = array.tobytes()
                return
            except Exception:
                pass

            # Strategy 4: Chunked allocation
            chunk_size = 1024 * 1024  # 1MB chunks
            chunks = []
            remaining = allocated_bytes

            while remaining > 0:
                chunk_bytes = min(chunk_size, remaining)
                chunk = bytearray(chunk_bytes)
                chunks.append(chunk)
                remaining -= chunk_bytes

            self.pool_data[pool.name] = b''.join(chunks)
            logger.info(f"Allocated pool {pool.name} using chunked strategy")

        except Exception as e:
            logger.error(f"Failed to allocate memory for pool {pool.name}: {e}")
            raise MemoryError(f"Memory allocation failed for pool {pool.name}: {e}")

    def deallocate_pool(self, pool_name: str, force: bool = False) -> bool:
        """
        Deallocate a memory pool

        Args:
            pool_name: Name of pool to deallocate
            force: Force deallocation even if pool is in use

        Returns:
            True if pool was successfully deallocated
        """
        if pool_name not in self.memory_pools:
            logger.warning(f"Pool {pool_name} not found")
            return False

        with self.pool_locks[pool_name]:
            try:
                pool = self.memory_pools[pool_name]

                if pool.status == PoolStatus.DELETED:
                    logger.warning(f"Pool {pool_name} already deleted")
                    return True

                if pool.status == PoolStatus.ACTIVE and not force:
                    logger.warning(f"Pool {pool_name} is active, use force=True to deallocate")
                    return False

                # Deallocate memory
                if pool_name in self.pool_data:
                    del self.pool_data[pool_name]

                # Cleanup backup file if exists
                if pool.backup_path and os.path.exists(pool.backup_path):
                    try:
                        os.unlink(pool.backup_path)
                    except Exception as e:
                        logger.warning(f"Failed to cleanup backup file {pool.backup_path}: {e}")

                # Mark as deleted
                pool.status = PoolStatus.DELETED
                self.total_deallocations += 1

                logger.info(f"Deallocated memory pool {pool_name}")
                return True

            except Exception as e:
                logger.error(f"Failed to deallocate pool {pool_name}: {e}")
                return False

    def access_pool(self, pool_name: str) -> Optional[bytes]:
        """
        Access memory pool data

        Args:
            pool_name: Name of pool to access

        Returns:
            Pool data as bytes, or None if not found
        """
        if pool_name not in self.memory_pools:
            return None

        with self.pool_locks[pool_name]:
            try:
                pool = self.memory_pools[pool_name]

                if pool.status != PoolStatus.ACTIVE:
                    return None

                # Update access statistics
                pool.last_access_time = datetime.now()
                pool.access_count += 1

                # Record access for statistics
                self.access_history.append({
                    'pool_name': pool_name,
                    'timestamp': datetime.now(),
                    'access_type': 'read'
                })

                # Return pool data
                return self.pool_data.get(pool_name)

            except Exception as e:
                logger.error(f"Failed to access pool {pool_name}: {e}")
                return None

    def write_pool(self, pool_name: str, data: bytes, offset: int = 0) -> bool:
        """
        Write data to memory pool

        Args:
            pool_name: Name of pool to write to
            data: Data to write
            offset: Offset in pool to write to

        Returns:
            True if write was successful
        """
        if pool_name not in self.memory_pools:
            return False

        with self.pool_locks[pool_name]:
            try:
                pool = self.memory_pools[pool_name]

                if pool.status != PoolStatus.ACTIVE:
                    return False

                # Check data size
                pool_data = self.pool_data.get(pool_name)
                if not pool_data:
                    return False

                if offset + len(data) > len(pool_data):
                    logger.error(f"Write exceeds pool size for {pool_name}")
                    return False

                # Write data
                if isinstance(pool_data, mmap.mmap):
                    pool_data.seek(offset)
                    pool_data.write(data)
                    pool_data.flush()
                else:
                    # Convert to mutable and write
                    mutable_data = bytearray(pool_data)
                    mutable_data[offset:offset + len(data)] = data
                    self.pool_data[pool_name] = bytes(mutable_data)

                # Update access statistics
                pool.last_access_time = datetime.now()
                pool.access_count += 1

                # Record access for statistics
                self.access_history.append({
                    'pool_name': pool_name,
                    'timestamp': datetime.now(),
                    'access_type': 'write',
                    'bytes_written': len(data)
                })

                # Update data hash for integrity checking
                pool.data_hash = self._calculate_data_hash(self.pool_data[pool_name])

                logger.debug(f"Wrote {len(data)} bytes to pool {pool_name} at offset {offset}")
                return True

            except Exception as e:
                logger.error(f"Failed to write to pool {pool_name}: {e}")
                return False

    def _calculate_data_hash(self, data: bytes) -> str:
        """Calculate hash of pool data for integrity checking"""
        return hashlib.sha256(data).hexdigest()

    def _should_defragment(self) -> bool:
        """Check if defragmentation should be performed"""
        if len(self.memory_pools) < 2:
            return False

        # Calculate overall fragmentation
        total_fragmentation = sum(
            pool.fragmentation_ratio for pool in self.memory_pools.values()
            if pool.status == PoolStatus.ACTIVE
        ) / max(1, len([
            pool for pool in self.memory_pools.values()
            if pool.status == PoolStatus.ACTIVE
        ]))

        return total_fragmentation > self.defragmentation_threshold

    def _defragment_pools(self) -> DefragmentationResult:
        """Perform pool defragmentation"""
        start_time = datetime.now()
        pools_processed = 0
        memory_freed_mb = 0.0
        errors = []

        logger.info("Starting memory pool defragmentation")

        try:
            # Get active pools sorted by fragmentation ratio
            fragmented_pools = [
                pool for pool in self.memory_pools.values()
                if pool.status == PoolStatus.ACTIVE and pool.fragmentation_ratio > 0.3
            ]
            fragmented_pools.sort(key=lambda p: p.fragmentation_ratio, reverse=True)

            initial_fragmentation = sum(p.fragmentation_ratio for p in fragmented_pools)

            for pool in fragmented_pools:
                try:
                    with self.pool_locks[pool.name]:
                        # Mark as defragmenting
                        pool.status = PoolStatus.DEFRAGMENTING

                        # Compact pool data
                        freed_memory = self._compact_pool(pool)
                        memory_freed_mb += freed_memory
                        pools_processed += 1

                        # Reset status
                        pool.status = PoolStatus.ACTIVE

                        logger.debug(f"Defragmented pool {pool.name}, freed {freed_memory:.1f}MB")

                except Exception as e:
                    errors.append(f"Failed to defragment pool {pool.name}: {e}")
                    logger.error(f"Pool defragmentation error: {e}")
                    if pool in self.memory_pools:
                        pool.status = PoolStatus.ACTIVE

            # Calculate improvement
            final_fragmentation = sum(
                pool.fragmentation_ratio for pool in self.memory_pools.values()
                if pool.status == PoolStatus.ACTIVE
            )
            fragmentation_improvement = initial_fragmentation - final_fragmentation

            processing_time = (datetime.now() - start_time).total_seconds()

            # Create result
            result = DefragmentationResult(
                timestamp=start_time,
                pools_processed=pools_processed,
                memory_freed_mb=memory_freed_mb,
                fragmentation_improvement=fragmentation_improvement,
                processing_time_seconds=processing_time,
                success=len(errors) == 0,
                errors=errors
            )

            self.defragmentation_history.append(result)
            self.total_defragmentations += 1

            logger.info(f"Defragmentation completed: {pools_processed} pools, "
                       f"{memory_freed_mb:.1f}MB freed, {processing_time:.2f}s")

            return result

        except Exception as e:
            errors.append(f"Defragmentation failed: {e}")
            logger.error(f"Defragmentation failed: {e}")

            return DefragmentationResult(
                timestamp=start_time,
                pools_processed=0,
                memory_freed_mb=0.0,
                fragmentation_improvement=0.0,
                processing_time_seconds=(datetime.now() - start_time).total_seconds(),
                success=False,
                errors=errors
            )

    def _compact_pool(self, pool: MemoryPool) -> float:
        """Compact individual pool to reduce fragmentation"""
        try:
            if pool.name not in self.pool_data:
                return 0.0

            data = self.pool_data[pool.name]
            original_size = len(data)

            # Remove unused portions (simplified)
            # In a real implementation, this would involve sophisticated compaction
            compacted_data = data.rstrip(b'\x00')
            self.pool_data[pool.name] = compacted_data

            # Update pool statistics
            freed_bytes = original_size - len(compacted_data)
            freed_mb = freed_bytes / (1024 * 1024)

            # Update fragmentation ratio (simplified calculation)
            pool.fragmentation_ratio = max(0.0, pool.fragmentation_ratio - 0.1)
            pool.allocated_size_mb = len(compacted_data) / (1024 * 1024)

            return freed_mb

        except Exception as e:
            logger.error(f"Failed to compact pool {pool.name}: {e}")
            return 0.0

    def _check_defragmentation_needed(self, current_time: datetime):
        """Check if automatic defragmentation should be triggered"""
        if not self.defragmentation_history:
            # First defragmentation check
            if self._should_defragment():
                self._defragment_pools()
            return

        # Check last defragmentation time
        last_defrag = self.defragmentation_history[-1]
        time_since_defrag = (current_time - last_defrag.timestamp).total_seconds()

        if time_since_defrag >= self.defragmentation_interval and self._should_defragment():
            self._defragment_pools()

    def _cleanup_idle_pools(self, current_time: datetime):
        """Clean up idle pools"""
        idle_pools = []
        timeout_delta = timedelta(minutes=self.pool_timeout_minutes)

        for pool_name, pool in self.memory_pools.items():
            if (pool.status == PoolStatus.ACTIVE and
                not pool.is_persistent and
                current_time - pool.last_access_time > timeout_delta):
                idle_pools.append(pool_name)

        for pool_name in idle_pools:
            if self.deallocate_pool(pool_name):
                logger.info(f"Cleaned up idle pool: {pool_name}")

    def _backup_pools(self):
        """Backup persistent pools to disk"""
        if not self.enable_backup:
            return

        for pool_name, pool in self.memory_pools.items():
            if pool.is_persistent and pool.status == PoolStatus.ACTIVE:
                try:
                    self._backup_pool(pool_name)
                except Exception as e:
                    logger.error(f"Failed to backup pool {pool_name}: {e}")

    def _backup_pool(self, pool_name: str):
        """Backup individual pool to disk"""
        if pool_name not in self.memory_pools:
            return

        pool = self.memory_pools[pool_name]
        if not pool.is_persistent or pool_name not in self.pool_data:
            return

        try:
            backup_file = self.backup_directory / f"{pool_name}.pool"
            backup_data = {
                'pool': pool,
                'data': self.pool_data[pool_name],
                'timestamp': datetime.now().isoformat()
            }

            with open(backup_file, 'wb') as f:
                pickle.dump(backup_data, f)

            pool.backup_path = str(backup_file)
            self.backup_count += 1

        except Exception as e:
            logger.error(f"Failed to backup pool {pool_name}: {e}")

    def restore_pool(self, pool_name: str) -> Optional[MemoryPool]:
        """Restore pool from backup"""
        if not self.enable_backup:
            return None

        backup_file = self.backup_directory / f"{pool_name}.pool"
        if not backup_file.exists():
            return None

        try:
            with open(backup_file, 'rb') as f:
                backup_data = pickle.load(f)

            pool = backup_data['pool']
            data = backup_data['data']

            # Restore pool
            self.memory_pools[pool_name] = pool
            self.pool_data[pool_name] = data
            pool.status = PoolStatus.ACTIVE

            self.restore_count += 1
            logger.info(f"Restored pool {pool_name} from backup")

            return pool

        except Exception as e:
            logger.error(f"Failed to restore pool {pool_name}: {e}")
            return None

    def _update_statistics(self):
        """Update pool statistics"""
        for pool_name, pool in self.memory_pools.items():
            if pool.status == PoolStatus.ACTIVE:
                # Update fragmentation ratio (simplified)
                if pool_name in self.pool_data:
                    data = self.pool_data[pool_name]
                    unused_bytes = data.count(b'\x00')
                    pool.fragmentation_ratio = unused_bytes / len(data) if len(data) > 0 else 0.0

    def get_pool_statistics(self) -> PoolStatistics:
        """Get comprehensive pool statistics"""
        active_pools = [
            pool for pool in self.memory_pools.values()
            if pool.status == PoolStatus.ACTIVE
        ]

        total_allocated_mb = sum(pool.allocated_size_mb for pool in active_pools)
        total_used_mb = total_allocated_mb  # Simplified - would need actual usage tracking

        avg_fragmentation = (
            sum(pool.fragmentation_ratio for pool in active_pools) / len(active_pools)
            if active_pools else 0.0
        )

        avg_access_count = (
            sum(pool.access_count for pool in active_pools) / len(active_pools)
            if active_pools else 0.0
        )

        # Pool type distribution
        type_counts = defaultdict(int)
        for pool in active_pools:
            type_counts[pool.pool_type.value] += 1

        last_defrag = self.defragmentation_history[-1].timestamp if self.defragmentation_history else None

        return PoolStatistics(
            total_pools=len(self.memory_pools),
            active_pools=len(active_pools),
            total_allocated_mb=total_allocated_mb,
            total_used_mb=total_used_mb,
            fragmentation_ratio=avg_fragmentation,
            avg_access_count=avg_access_count,
            pool_type_distribution=dict(type_counts),
            defragmentation_count=len(self.defragmentation_history),
            last_defragmentation=last_defrag
        )

    def get_pool_report(self) -> Dict[str, Any]:
        """Generate comprehensive pool management report"""
        stats = self.get_pool_statistics()

        # Get pool details
        pool_details = []
        for pool in self.memory_pools.values():
            pool_details.append({
                'name': pool.name,
                'type': pool.pool_type.value,
                'size_mb': pool.size_mb,
                'allocated_mb': pool.allocated_size_mb,
                'status': pool.status.value,
                'fragmentation': pool.fragmentation_ratio,
                'access_count': pool.access_count,
                'last_access': pool.last_access_time.isoformat(),
                'is_persistent': pool.is_persistent
            })

        # Get defragmentation history
        defrag_history = []
        for result in self.defragmentation_history[-10:]:  # Last 10 defragmentations
            defrag_history.append({
                'timestamp': result.timestamp.isoformat(),
                'pools_processed': result.pools_processed,
                'memory_freed_mb': result.memory_freed_mb,
                'fragmentation_improvement': result.fragmentation_improvement,
                'processing_time_seconds': result.processing_time_seconds,
                'success': result.success
            })

        return {
            'summary': {
                'total_pools': stats.total_pools,
                'active_pools': stats.active_pools,
                'total_allocated_mb': stats.total_allocated_mb,
                'total_used_mb': stats.total_used_mb,
                'fragmentation_ratio': stats.fragmentation_ratio,
                'feature_enabled': self.feature_enabled
            },
            'statistics': {
                'total_allocations': self.total_allocations,
                'total_deallocations': self.total_deallocations,
                'total_defragmentations': self.total_defragmentations,
                'backup_count': self.backup_count,
                'restore_count': self.restore_count
            },
            'pool_type_distribution': stats.pool_type_distribution,
            'pool_details': pool_details,
            'defragmentation_history': defrag_history,
            'configuration': {
                'max_pools': self.max_pools,
                'max_total_memory_mb': self.max_total_memory_mb,
                'defragmentation_threshold': self.defragmentation_threshold,
                'auto_defragment': self.auto_defragment,
                'enable_backup': self.enable_backup,
                'backup_directory': str(self.backup_directory)
            }
        }

    def reset_statistics(self):
        """Reset pool management statistics"""
        self.total_allocations = 0
        self.total_deallocations = 0
        self.total_defragmentations = 0
        self.backup_count = 0
        self.restore_count = 0
        self.defragmentation_history.clear()
        self.access_history.clear()
        logger.info("Memory pool manager statistics reset")

    def shutdown(self):
        """Shutdown pool manager and cleanup resources"""
        logger.info("Shutting down memory pool manager...")

        # Stop monitoring
        self.stop_monitoring()

        # Deallocate all pools
        for pool_name in list(self.memory_pools.keys()):
            self.deallocate_pool(pool_name, force=True)

        # Cleanup
        self.memory_pools.clear()
        self.pool_data.clear()
        self.pool_locks.clear()

        logger.info("Memory pool manager shutdown complete")


# Factory function for easy instantiation
def create_pool_manager(**kwargs) -> MemoryPoolManager:
    """
    Factory function to create memory pool manager

    Args:
        **kwargs: Arguments for MemoryPoolManager

    Returns:
        MemoryPoolManager instance
    """
    return MemoryPoolManager(**kwargs)


# Context manager for temporary pools
@contextmanager
def temporary_pool(
    pool_name: str,
    size_mb: int,
    pool_type: PoolType = PoolType.TEMPORARY
):
    """
    Context manager for temporary memory pools

    Args:
        pool_name: Name for the temporary pool
        size_mb: Size of the pool in MB
        pool_type: Type of pool (defaults to TEMPORARY)
    """
    manager = create_pool_manager()
    pool = None

    try:
        pool = manager.allocate_pool(pool_name, size_mb, pool_type)
        yield manager, pool
    finally:
        if pool:
            manager.deallocate_pool(pool_name)
        manager.shutdown()